#!/usr/bin/env python

import sys
import argparse
import logging
import textwrap
from typing import cast, Any

from collections import defaultdict, Counter

from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource
from dae.annotation.annotation_factory import \
    build_annotation_pipeline

from dae.annotation.annotatable import VCFAllele

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.tools.stats_liftover import save_liftover_stats

logger = logging.getLogger("denovo_liftover")


def parse_cli_arguments(argv):
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="liftover denovo to hg38")

    VerbosityConfiguration.set_argumnets(parser)
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


def main(argv=None, gpf_instance=None):
    """Liftover de Novo variants tool main function."""
    # pylint: disable=too-many-locals
    if argv is None:
        argv = sys.argv[1:]
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    argv = parse_cli_arguments(argv)

    VerbosityConfiguration.set(argv)
    grr = build_genomic_resource_repository()
    source_genome = build_reference_genome_from_resource(
        grr.get_resource(argv.source_genome))
    assert source_genome is not None
    source_genome.open()

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
    pipeline.open()

    target_stats: dict[str, Any] = defaultdict(Counter)

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

            source_worst_effect = cast(str, result.get("source_worst_effect"))
            target_worst_effect = cast(str, result.get("target_worst_effect"))
            target_stats[source_worst_effect]["source"] += 1

            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
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
