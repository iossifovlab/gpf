#!/usr/bin/env python

import os
import sys
import argparse
import logging

from dae.parquet.schema1.parquet_io import (
    ParquetPartitionDescriptor,
    ParquetManager,
)
from dae.pedigrees.loader import FamiliesLoader


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('--verbose', '-V', action='count', default=0)

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
    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    run(argv)


def run(argv):
    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    if argv.study_id is not None:
        study_id = argv.study_id
    else:
        study_id, _ = os.path.splitext(os.path.basename(filename))

    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    if argv.partition_description:
        partition_description = ParquetPartitionDescriptor.from_config(
            argv.partition_description
        )
        if partition_description.family_bin_size > 0:
            families = partition_description \
                .add_family_bins_to_families(families)

    if not argv.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(filename))
        output_filename = f"{output_filename}.parquet"
    else:
        output_filename = argv.output_filename

    ParquetManager.families_to_parquet(families, output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
