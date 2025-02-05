import argparse
import logging
import sys

from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
    build_genomic_resource_repository,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants_loaders.dae.loader import DaeTransmittedLoader
from dae.variants_loaders.vcf.serializer import VcfSerializer

logger = logging.getLogger("dae2vcf")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="Convert transmitted DAE variants into VCF file format")

    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    DaeTransmittedLoader.cli_arguments(parser)

    parser.add_argument(
        "-g", "--genome", help="reference genome resource ID",
        default="hg38/genomes/GRCh38-hg38")

    parser.add_argument(
        "-o", "--output", help="output filename",
        default=None)

    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """Convert transmitted DAE variants into VCF file format."""
    # pylint: disable=too-many-locals
    if argv is None:
        argv = sys.argv[1:]
    if grr is None:
        grr = build_genomic_resource_repository()

    args = parse_cli_arguments(argv)

    VerbosityConfiguration.set(args)
    genome = build_reference_genome_from_resource(
        grr.get_resource(args.genome))
    assert genome is not None
    genome.open()

    families_filenames, families_params = \
        FamiliesLoader.parse_cli_arguments(args)
    families_filename = families_filenames[0]

    families_loader = FamiliesLoader(
        families_filename, **families_params,
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        DaeTransmittedLoader.parse_cli_arguments(args)

    variants_loader = DaeTransmittedLoader(
        families,
        variants_filenames,  # type: ignore
        params=variants_params,
        genome=genome,
    )

    vcf_serializer = VcfSerializer(
        families,
        genome,
        args.output,
        header=[
            f"##source=dae2vcf {' '.join(argv)}",
        ],
    )

    with vcf_serializer as serializer:
        serializer.serialize(variants_loader.full_variants_iterator())
