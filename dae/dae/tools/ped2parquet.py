#!/usr/bin/env python

import os
import sys
import argparse

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.pedigrees.loader import FamiliesLoader
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema1.parquet_io import ParquetManager


def main(argv):
    """Entry point for ped2parquet."""
    parser = argparse.ArgumentParser()

    VerbosityConfiguration.set_argumnets(parser)

    FamiliesLoader.cli_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        dest="output_filename",
        help="output families parquet filename "
        "(default is [basename(families_filename).parquet])",
    )
    parser.add_argument(
        "--partition-description",
        "--pd",
        help="input partition description filename",
    )
    parser.add_argument(
        "--study-id",
        type=str,
        default=None,
        dest="study_id",
        metavar="<study id>",
        help="Study ID. "
        "If none specified, the basename of families filename is used to "
        "construct study id [default: basename(families filename)]",
    )
    argv = parser.parse_args(argv)
    VerbosityConfiguration.set(argv)
    run(argv)


def run(argv):
    """Run the ped to parquet conversion."""
    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    # if argv.study_id is not None:
    #     study_id = argv.study_id
    # else:
    #     study_id, _ = os.path.splitext(os.path.basename(filename))

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    if argv.partition_description:
        partition_description = PartitionDescriptor.parse(
            argv.partition_description)
    else:
        partition_description = PartitionDescriptor()

    if not argv.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(filename))
        output_filename = f"{output_filename}.parquet"
    else:
        output_filename = argv.output_filename

    ParquetManager.families_to_parquet(
        families, output_filename, partition_description)


if __name__ == "__main__":
    main(sys.argv[1:])
