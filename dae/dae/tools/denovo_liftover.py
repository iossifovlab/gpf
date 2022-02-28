#!/usr/bin/env python

import sys
import argparse
import logging
import textwrap
from typing import cast

from collections import defaultdict, Counter

from dae.utils.variant_utils import mat2str
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource
from dae.annotation.annotation_factory import \
    build_annotation_pipeline

from dae.annotation.annotatable import VCFAllele

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader


logger = logging.getLogger("denovo_liftover")


def parse_cli_arguments(argv):
    parser = argparse.ArgumentParser(description="liftover denovo to hg38")

    parser.add_argument('--verbose', '-V', action='count', default=0)

    FamiliesLoader.cli_arguments(parser)
    DenovoLoader.cli_arguments(parser)

    parser.add_argument(
        "-c", "--chain", help="chain resource id",
        default="liftover/hg19ToHg38")

    parser.add_argument(
        "-t", "--target-genome", help="target genome",
        default="hg38/genomes/GRCh38-hg38")
    parser.add_argument(
        "--target-gene-models", "--tgm", help="target gene models",
        default="hg38/gene_models/refGene_v20170601")

    parser.add_argument(
        "-s", "--source-genome", help="source genome",
        default="hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")
    parser.add_argument(
        "--source-gene-models", "--sgm", help="source gene models",
        default="hg19/gene_models/refGene_v20190211")

    parser.add_argument(
        "--stats", help="filename to store liftover statistics",
        default="stats.txt"
    )

    parser.add_argument(
        "-o", "--output", help="output filename",
        default="denovo_liftover.txt")

    argv = parser.parse_args(argv)
    return argv


def save_liftover_stats(target_stats, stats_filename):

    effects = [
        "CNV+",
        "CNV-",
        "tRNA:ANTICODON",
        "all",
        "splice-site",
        "frame-shift",
        "nonsense",
        "no-frame-shift-newStop",
        "noStart",
        "noEnd",
        "missense",
        "no-frame-shift",
        "CDS",
        "synonymous",
        "coding_unknown",
        "regulatory",
        "3'UTR",
        "5'UTR",
        "intron",
        "non-coding",
        "5'UTR-intron",
        "3'UTR-intron",
        "promoter",
        "non-coding-intron",
        "unknown",
        "intergenic",
        "no-mutation",
    ]

    effects = [e for e in effects if e in target_stats.keys()]
    assert len(effects) == len(target_stats.keys())

    with open(stats_filename, "w") as output:
        header = list(["source", *effects])

        output.write("\t".join(header))
        output.write("\n")

        line = list(
            [
                "source",
                *[str(target_stats[e]["source"]) for e in effects]
            ]
        )
        output.write("\t".join(line))
        output.write("\n")

        for target in ["no_liftover", *effects]:
            line = [target]
            for source in effects:
                line.append(str(target_stats[source].get(target, "")))
            output.write("\t".join(line))
            output.write("\n")


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    argv = parse_cli_arguments(argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("dae.effect_annotation").setLevel(logging.WARNING)

    grr = gpf_instance.grr
    source_genome_resource = grr.get_resource(argv.source_genome)
    assert source_genome_resource is not None
    source_genome = open_reference_genome_from_resource(source_genome_resource)
    assert source_genome is not None

    families_filename, families_params = \
        FamiliesLoader.parse_cli_arguments(argv)

    families_loader = FamiliesLoader(
        families_filename, **families_params
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        DenovoLoader.parse_cli_arguments(argv)

    variants_loader = DenovoLoader(
        families,
        variants_filenames,
        params=variants_params,
        genome=source_genome,
    )

    pipeline_config = textwrap.dedent(
        f"""
        - effect_annotator:
            gene_models: {argv.source_gene_models}
            genome: {argv.source_genome}
            attributes:
            - source: "worst_effect"
              destination: "source_worst_effect"
            - source: "gene_effects"
              destination: "source_gene_effects"
            - source: "effect_details"
              destination: "source_effect_details"

        - liftover_annotator:
            chain: {argv.chain}
            target_genome: {argv.target_genome}
            attributes:
            - source: liftover_annotatable
              destination: target_annotatable

        - effect_annotator:
            gene_models: {argv.target_gene_models}
            genome: {argv.target_genome}
            input_annotatable: target_annotatable
            attributes:
            - source: "worst_effect"
              destination: "target_worst_effect"
            - source: "gene_effects"
              destination: "target_gene_effects"
            - source: "effect_details"
              destination: "target_effect_details"

        """
    )

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=gpf_instance.grr)

    target_stats = defaultdict(Counter)

    with open(argv.output, "wt") as output:

        header = [
            "chrom38", "pos38", "ref38", "alt38",  # "location38", "variant38",
            "chrom19", "pos19", "ref19", "alt19",  # "location19", "variant19",
            "familyId", "bestSt",
        ]

        output.write("\t".join(header))
        output.write("\n")

        for sv, fvs in variants_loader.full_variants_iterator():
            assert len(sv.alt_alleles) == 1

            aa = sv.alt_alleles[0]
            annotatable: VCFAllele = cast(VCFAllele, aa.get_annotatable())
            result = pipeline.annotate(annotatable)
            liftover_annotatable: VCFAllele = \
                cast(VCFAllele, result.get("target_annotatable"))

            source_worst_effect = result.get("source_worst_effect")
            target_worst_effect = result.get("target_worst_effect")
            target_stats[source_worst_effect]["source"] += 1

            if liftover_annotatable is None:
                logger.error(f"can't liftover {aa}")
                target_stats[source_worst_effect]["no_liftover"] += 1
                continue

            target_stats[source_worst_effect][target_worst_effect] += 1

            for fv in fvs:
                fa = fv.alt_alleles[0]

                line = [
                    liftover_annotatable.chrom, str(liftover_annotatable.pos),
                    liftover_annotatable.ref, liftover_annotatable.alt,

                    annotatable.chrom, str(annotatable.pos),
                    annotatable.ref, annotatable.alt,

                    fa.family_id,
                    mat2str(fa.best_state, col_sep=" "),
                ]
                output.write("\t".join(line))
                output.write("\n")


    save_liftover_stats(target_stats, argv.stats)

if __name__ == "__main__":
    main(sys.argv[1:])
