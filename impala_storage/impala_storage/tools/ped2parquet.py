#!/usr/bin/env python

import os
import sys
import argparse

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.pedigrees.loader import FamiliesLoader
from dae.parquet.partition_descriptor import PartitionDescriptor
from impala_storage.schema1.parquet_io import VariantsParquetWriter, \
    ParquetWriter


def main(argv: list[str]) -> None:
    """Entry point for ped2parquet."""
    parser = argparse.ArgumentParser()

    VerbosityConfiguration.set_arguments(parser)

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
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)
    run(args)


def run(args: argparse.Namespace) -> None:
    """Run the ped to parquet conversion."""
    filenames, params = FamiliesLoader.parse_cli_arguments(args)
    filename = filenames[0]

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    if args.partition_description:
        partition_description = PartitionDescriptor.parse(
            args.partition_description)
    else:
        partition_description = PartitionDescriptor()

    if not args.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(filename))
        output_filename = f"{output_filename}.parquet"
    else:
        output_filename = args.output_filename

    ParquetWriter.families_to_parquet(
        families, output_filename,
        VariantsParquetWriter,
        partition_description)


if __name__ == "__main__":
    main(sys.argv[1:])
