#!/usr/bin/env python
"""Tool to convert pedigree file into cannonical GPF pedigree file."""

import os
import sys
import argparse
import logging
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.genomic_resources.genomic_context import CLIGenomicContext, \
    get_genomic_context

logger = logging.getLogger("ped2ped")


def _handle_partition_description(families, argv):
    if argv.partition_description:
        partition_descriptor = PartitionDescriptor.parse(
            argv.partition_description
        )
        for family in families.values():
            family_bin = partition_descriptor.make_family_bin(
                family.family_id)
            for person in family.persons.values():
                person.set_attr("family_bin", family_bin)
        families._ped_df = None  # pylint: disable=protected-access

    return families


def _handle_vcf_files(families, argv):
    variants_filenames, variants_params = \
        VcfLoader.parse_cli_arguments(argv)

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

        families = variants_loader.families
    return families


def main(argv):
    """Transform a pedigree file into cannonical GPF pedigree.

    It should be called from the command line.
    """
    parser = argparse.ArgumentParser()
    VerbosityConfiguration.set_argumnets(parser)
    FamiliesLoader.cli_arguments(parser)
    VcfLoader.cli_arguments(parser, options_only=True)
    CLIGenomicContext.add_context_arguments(parser)

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

    argv = parser.parse_args(argv)
    VerbosityConfiguration.set(argv)
    CLIGenomicContext.register(argv)

    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    logger.info("PED PARAMS: %s", params)

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    families = _handle_partition_description(families, argv)
    families = _handle_vcf_files(families, argv)

    if families.broken_families:
        for family_id, family in families.broken_families.items():
            if not family.has_members():
                del families[family_id]
                logger.warning(
                    "family %s does not contain sequenced members "
                    "and is removed from the pedigree: %s", family_id, family)

    if not argv.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(filename))
        output_filename = f"{output_filename}.ped"
    elif argv.output_filename == "-":
        output_filename = sys.stdout
    else:
        output_filename = argv.output_filename

    FamiliesLoader.save_pedigree(families, output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
