#!/usr/bin/env python

import os
import argparse
from dae.backends.impala.parquet_io import \
    ParquetPartitionDescription, save_ped_df_to_parquet
from dae.pedigrees.family import PedigreeReader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'pedigree',
        help='input pedigree filename'
    )
    parser.add_argument(
        '-o',
        dest='output_filename',
        help='output filename (default is [input filename]_parquet.ped)'
    )
    parser.add_argument(
        '--partition-description',
        help='input partition description filename'
    )
    args = parser.parse_args()

    ped_df = PedigreeReader.flexible_pedigree_read(
        pedigree_filepath=args.pedigree
    )

    if args.partition_description:
        partition_description = ParquetPartitionDescription.from_config(
            args.partition_description
        )
        ped_df = partition_description.add_family_bins_to_pedigree_df(ped_df)

    if not args.output_filename:
        output_filename, _ = os.path.splitext(os.path.basename(args.pedigree))
        output_filename = f'{output_filename}_parquet.ped'
    else:
        output_filename = args.output_filename

    save_ped_df_to_parquet(ped_df, output_filename)


if __name__ == '__main__':
    main()
