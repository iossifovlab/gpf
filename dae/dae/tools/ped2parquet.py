#!/usr/bin/env python

import os
import sys
import argparse
from dae.backends.impala.parquet_io import \
    ParquetPartitionDescription, ParquetManager
from dae.pedigrees.loader import FamiliesLoader


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'pedigree',
        help='input pedigree filename'
    )
    parser.add_argument(
        '-o',
        dest='output_filename',
        help='output pedigree parquet filename '
        '(default is [basename(pedigree)].parquet)'
    )
    parser.add_argument(
        '--partition-description', '--pd',
        help='input partition description filename'
    )
    FamiliesLoader.cli_arguments(parser)
    args = parser.parse_args(argv)

    params = FamiliesLoader.parse_cli_arguments(args)

    loader = FamiliesLoader(
        args.pedigree,
        params=params
    )
    families = loader.load()

    if args.partition_description:
        partition_description = ParquetPartitionDescription.from_config(
            args.partition_description
        )
        families = partition_description.add_family_bins_to_families(families)

    if not args.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(args.pedigree))
        output_filename = f'{output_filename}.parquet'
    else:
        output_filename = args.output_filename

    ParquetManager.families_to_parquet(families, output_filename)


if __name__ == '__main__':
    main(sys.argv)
