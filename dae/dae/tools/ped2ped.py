"""Tool to convert pedigree file into cannonical GPF pedigree file."""

import argparse
import logging
import os
import sys

from dae.genomic_resources.genomic_context import (
    context_providers_init,
    get_genomic_context,
)
from dae.genomic_resources.genomic_context_cli import (
    CLIGenomicContextProvider,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader, PedigreeIO
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants_loaders.vcf.loader import VcfLoader

logger = logging.getLogger("ped2ped")


def _handle_partition_description(
    families: FamiliesData, args: argparse.Namespace,
) -> FamiliesData:
    if args.partition_description:
        partition_descriptor = PartitionDescriptor.parse(
            args.partition_description,
        )
        for family in families.values():
            family_bin = partition_descriptor.make_family_bin(
                family.family_id)
            for person in family.persons.values():
                person.set_attr("family_bin", family_bin)
        families._ped_df = None  # noqa pylint: disable=protected-access

    return families


def _handle_vcf_files(
    families: FamiliesData, args: argparse.Namespace,
) -> FamiliesData:
    variants_filenames, variants_params = \
        VcfLoader.parse_cli_arguments(args)

    if variants_filenames:
        assert variants_filenames is not None

        context = get_genomic_context()
        genome = context.get_reference_genome()
        if genome is None:
            raise ValueError("unable to find reference genome")

        variants_loader = VcfLoader(
            families,
            variants_filenames,
            params=variants_params,
            genome=genome,
        )
        variants_loader.init_vcf_loaders()

        families = variants_loader.families
    return families


def main(argv: list[str] | None = None) -> None:
    """Transform a pedigree file into cannonical GPF pedigree.

    It should be called from the command line.
    """
    parser = argparse.ArgumentParser()
    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    VcfLoader.cli_arguments(parser, options_only=True)
    CLIGenomicContextProvider.add_argparser_arguments(parser)

    parser.add_argument(
        "-o",
        "--output",
        dest="output_filename",
        help="output families parquet filename "
        "(default is [basename(families_filename).ped])",
    )
    parser.add_argument(
        "--partition-description",
        "--pd",
        help="input partition description filename",
    )
    parser.add_argument(
        "--vcf-files",
        type=str,
        nargs="+",
        metavar="<VCF filename>",
        help="VCF file to import",
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)
    context_providers_init(**vars(args))
    filenames, params = FamiliesLoader.parse_cli_arguments(args)
    filename = filenames[0]

    logger.info("PED PARAMS: %s", params)

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    families = _handle_partition_description(families, args)
    families = _handle_vcf_files(families, args)

    if families.broken_families:
        for family_id, family in families.broken_families.items():
            if not family.has_members() and family_id in families:
                del families[family_id]
                logger.warning(
                    "family %s does not contain sequenced members "
                    "and is removed from the pedigree: %s", family_id, family)

    families.redefine()

    output_filename: PedigreeIO
    if not args.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(filename))
        output_filename = f"{output_filename}.ped"
    elif args.output_filename == "-":
        output_filename = sys.stdout
    else:
        output_filename = args.output_filename

    FamiliesLoader.save_pedigree(families, output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
