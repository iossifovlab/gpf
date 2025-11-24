import argparse
import logging
import sys
import textwrap
from typing import cast

from dae.annotation.annotatable import CNVAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.cnv.loader import CNVLoader

logger = logging.getLogger("cnv_liftover")


def build_cli_arguments_parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="liftover CNV variants")

    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    CNVLoader.cli_arguments(parser)

    context_providers_add_argparser_arguments(
        parser,
        skip_cli_annotation_context=True,
    )

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
        "-o", "--output", help="output filename",
        default="cnv_liftover.txt")

    parser.add_argument(
        "--mode",
        type=str,
        dest="mode",
        metavar="mode",
        default="bcf_liftover",
        help="mode to use for liftover: 'bcf_liftover' or 'basic_liftover'",
    )

    return parser


def build_liftover_pipeline(
    mode: str,
    source_genome: str,
    target_genome: str,
    chain: str,
    grr: GenomicResourceRepo,
) -> AnnotationPipeline:
    """Build liftover annotator based on the selected mode."""
    if mode not in {"bcf_liftover", "basic_liftover"}:
        raise ValueError(f"unknown liftover mode: {mode}")
    annotator_type = "liftover_annotator"
    if mode == "basic_liftover":
        annotator_type = "basic_liftover_annotator"

    pipeline_config = textwrap.dedent(
        f"""
        - {annotator_type}:
            chain: {chain}
            source_genome: {source_genome}
            target_genome: {target_genome}
            attributes:
            - source: liftover_annotatable
              name: target_annotatable
        """,
    )

    pipeline = load_pipeline_from_yaml(pipeline_config, grr)
    pipeline.open()

    return pipeline


def main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """Liftover de Novo variants tool main function."""
    # pylint: disable=too-many-locals
    if argv is None:
        argv = sys.argv[1:]
    parser = build_cli_arguments_parser()
    assert argv is not None
    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)
    context_providers_init(
        **vars(args), skip_cli_annotation_context=True)
    genomic_context = get_genomic_context()

    if grr is None:
        grr = genomic_context.get_genomic_resources_repository()
    if grr is None:
        raise ValueError("no valid GRR configured")

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
    pipeline = build_liftover_pipeline(
        args.mode,
        args.source_genome,
        args.target_genome,
        args.chain,
        grr,
    )

    with open(args.output, "wt") as output:

        header = [
            "location", "cnv_type",
            "location_src", "cnv_type_src",
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
                continue

            for fv in fvs:
                size_src = len(annotatable)
                size = len(liftover_annotatable)

                size_diff = (100.0 * abs(size_src - size)) / size_src
                if size_diff >= 50:
                    logger.warning(
                        "CNV variant size changed more than 50 percent: %s; "
                        "%s -> %s",
                        size_diff, annotatable, liftover_annotatable)

                for aa in fv.alt_alleles:
                    fa = cast(FamilyAllele, aa)
                    line: list[str] = []
                    person_ids = [
                        person_id
                        for person_id in fa.variant_in_members
                        if person_id is not None
                    ]
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
