#!/usr/bin/env python

import argparse
import logging
import sys
import textwrap
from collections import Counter, defaultdict
from typing import Any, cast

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.tools.stats_liftover import save_liftover_stats
from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.dae.loader import DenovoLoader

logger = logging.getLogger("denovo_liftover")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="liftover denovo variants")

    VerbosityConfiguration.set_arguments(parser)
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
        default="stats.txt",
    )

    parser.add_argument(
        "-o", "--output", help="output filename",
        default="denovo_liftover.txt")

    return parser.parse_args(argv)


def main(
        argv: list[str] | None = None,
        gpf_instance: GPFInstance | None = None) -> None:
    """Liftover de Novo variants tool main function."""
    # pylint: disable=too-many-locals
    if argv is None:
        argv = sys.argv[1:]
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    args = parse_cli_arguments(argv)

    VerbosityConfiguration.set(args)
    grr = build_genomic_resource_repository()
    source_genome = build_reference_genome_from_resource(
        grr.get_resource(args.source_genome))
    assert source_genome is not None
    source_genome.open()

    families_filenames, families_params = \
        FamiliesLoader.parse_cli_arguments(args)
    families_filename = families_filenames[0]

    families_loader = FamiliesLoader(
        families_filename, **families_params,
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        DenovoLoader.parse_cli_arguments(args)

    variants_loader = DenovoLoader(
        families,
        variants_filenames,  # type: ignore
        params=variants_params,
        genome=source_genome,
    )

    pipeline_config = textwrap.dedent(
        f"""
        - effect_annotator:
            gene_models: {args.source_gene_models}
            genome: {args.source_genome}
            attributes:
            - source: "worst_effect"
              name: "source_worst_effect"
            - source: "gene_effects"
              name: "source_gene_effects"
            - source: "effect_details"
              name: "source_effect_details"

        - liftover_annotator:
            chain: {args.chain}
            source_genome: {args.source_genome}
            target_genome: {args.target_genome}
            attributes:
            - source: liftover_annotatable
              name: target_annotatable

        - effect_annotator:
            gene_models: {args.target_gene_models}
            genome: {args.target_genome}
            input_annotatable: target_annotatable
            attributes:
            - source: "worst_effect"
              name: "target_worst_effect"
            - source: "gene_effects"
              name: "target_gene_effects"
            - source: "effect_details"
              name: "target_effect_details"

        """,
    )

    pipeline = load_pipeline_from_yaml(pipeline_config, gpf_instance.grr)
    pipeline.open()

    target_stats: dict[str, Any] = defaultdict(Counter)

    with open(args.output, "wt") as output:

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
                fa = cast(FamilyAllele, fv.alt_alleles[0])

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

    save_liftover_stats(target_stats, args.stats)
