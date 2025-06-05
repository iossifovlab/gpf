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
from dae.variants_loaders.vcf.loader import VcfLoader

logger = logging.getLogger("vcf2tsv")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="save VCF variants into TSV file")

    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    VcfLoader.cli_arguments(parser)

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
    """Liftover de Novo variants tool main function."""
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
        VcfLoader.parse_cli_arguments(args)

    variants_loader = VcfLoader(
        families,
        variants_filenames,
        params=variants_params,
        genome=genome,
    )
    with open(args.output, "wt") if args.output else \
            open(sys.stdout.fileno(), "wt", closefd=False) as output:
        print(
            "chrom", "pos", "ref", "alt", "family_id", "person_id",
            file=output, sep="\t")
        for fv in variants_loader.family_variants_iterator():
            for fa in fv.family_alt_alleles:
                print(
                    fa.chrom, fa.position, fa.reference, fa.alternative,
                    fa.family_id,
                    ",".join(m for m in fa.allele_in_members if m is not None),
                    file=output, sep="\t")
