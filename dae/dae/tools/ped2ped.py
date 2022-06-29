#!/usr/bin/env python
"""Tool to convert pedigree file into cannonical GPF pedigree file."""

import os
import sys
import argparse
import logging
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor
from dae.pedigrees.loader import FamiliesLoader
from dae.backends.vcf.loader import VcfLoader
from dae.gpf_instance.gpf_instance import GPFInstance


logger = logging.getLogger("ped2ped")


def _handle_partition_description(families, argv):
    if argv.partition_description:
        partition_description = ParquetPartitionDescriptor.from_config(
            argv.partition_description
        )
        families = partition_description.add_family_bins_to_families(families)
    return families


def _handle_vcf_files(families, argv, gpf_instance):
    variants_filenames, variants_params = \
        VcfLoader.parse_cli_arguments(argv)

    if variants_filenames:
        assert variants_filenames is not None

        variants_loader = VcfLoader(
            families,
            variants_filenames,
            params=variants_params,
            genome=gpf_instance.reference_genome,
        )

        families = variants_loader.families
    return families


def main(argv, gpf_instance=None):
    """Transform a pedigree file into cannonical GPF pedigree.

    It should be called from the command line.
    """
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-V", action="count", default=0)

    FamiliesLoader.cli_arguments(parser)
    VcfLoader.cli_arguments(parser, options_only=True)

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
    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    logger.info("PED PARAMS: %s", params)

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    families = _handle_partition_description(families, argv)
    families = _handle_vcf_files(families, argv, gpf_instance)

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
