#!/usr/bin/env python

import argparse
import logging
import sys
import textwrap
from typing import cast

from dae.annotation.annotatable import CNVAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.statistics import StatsCollection
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.cnv.loader import CNVLoader

logger = logging.getLogger("denovo_liftover")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="liftover CNV variants")

    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    CNVLoader.cli_arguments(parser)

    parser.add_argument(
        "-c", "--chain", help="chain resource id",
        default="liftover/hg19ToHg38")

    parser.add_argument(
        "-t", "--target-genome", help="target genome",
        default="hg38/genomes/GRCh38-hg38")

    parser.add_argument(
        "-s", "--source-genome", help="source genome",
        default="hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")

    parser.add_argument(
        "--stats", help="filename to store liftover statistics",
        default="stats.txt",
    )

    parser.add_argument(
        "-o", "--output", help="output filename",
        default="cnv_liftover.txt")

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
        CNVLoader.parse_cli_arguments(args)

    variants_loader = CNVLoader(
        families,
        variants_filenames,  # type: ignore
        params=variants_params,
        genome=source_genome,
    )

    pipeline_config = textwrap.dedent(
        f"""
        - liftover_annotator:
            chain: {args.chain}
            source_genome: {args.source_genome}
            target_genome: {args.target_genome}
            attributes:
            - source: liftover_annotatable
              name: target_annotatable
        """,
    )

    pipeline = load_pipeline_from_yaml(pipeline_config, gpf_instance.grr)
    pipeline.open()

    stats: StatsCollection = StatsCollection()

    with open(args.output, "wt") as output:

        header = [
            "location38", "cnv_type38",
            "location19", "cnv_type19",
            "size_change",
            "familyId", "personId",
        ]

        output.write("\t".join(header))
        output.write("\n")

        for sv, fvs in variants_loader.full_variants_iterator():
            assert len(sv.alt_alleles) == 1

            aa = sv.alt_alleles[0]
            annotatable: CNVAllele = cast(CNVAllele, aa.get_annotatable())
            result = pipeline.annotate(annotatable)
            liftover_annotatable: CNVAllele = \
                cast(CNVAllele, result.get("target_annotatable"))

            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
                stats.inc(("no_liftover", ))
                continue

            for fv in fvs:
                stats.inc(("liftover", ))
                stats.inc((
                    annotatable.type.name,
                    liftover_annotatable.type.name))
                size19 = len(annotatable)
                size38 = len(liftover_annotatable)

                size_diff = (100.0 * abs(size19 - size38)) / size19
                if size_diff >= 50:
                    logger.warning(
                        "CNV variant changed more than 50 percent: %s; "
                        "%s -> %s",
                        size_diff, annotatable, liftover_annotatable)

                stats.inc((f"size_diff: {int(size_diff / 10) * 10}", ))

                for aa in fv.alt_alleles:
                    fa = cast(FamilyAllele, aa)
                    line: list[str] = []
                    person_ids = []
                    for person_id in fa.variant_in_members:
                        if person_id is not None:
                            person_ids.append(person_id)
                    assert len(person_ids) >= 1
                    line = [
                        f"{liftover_annotatable.chrom}:"
                        f"{liftover_annotatable.pos}-"
                        f"{liftover_annotatable.pos_end}",
                        liftover_annotatable.type.name,

                        f"{annotatable.chrom}:"
                        f"{annotatable.pos}-"
                        f"{annotatable.pos_end}",
                        annotatable.type.name,
                        str(size_diff),
                        fa.family_id,
                        ";".join(person_ids),
                    ]

                    output.write("\t".join(line))
                    output.write("\n")
                    stats.inc(("output", ))

    stats.save(args.stats)
