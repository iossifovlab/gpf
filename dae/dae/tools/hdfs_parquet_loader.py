#!/usr/bin/env python
import os
import sys
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.impala_storage.parquet_io import NoPartitionDescriptor, \
    ParquetPartitionDescriptor


logger = logging.getLogger("hdfs_parquet_loader")


def parse_cli_arguments(argv, gpf_instance):
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--verbose', '-V', action='count', default=0)

    parser.add_argument(
        "study_id",
        type=str,
        metavar="<study ID>",
        help="study ID to be loaded",
    )

    parser.add_argument(
        "pedigree",
        type=str,
        metavar="<Pedigree Filepath>",
        help="path to the pedigree file",
    )

    parser.add_argument(
        "--variants",
        type=str,
        metavar="<Variants Parquet Directory>",
        help="path to directory which contains variants parquet data files",
    )

    default_genotype_storage_id = (
        gpf_instance.dae_config.genotype_storage.default
    )

    parser.add_argument(
        "--genotype-storage",
        "--gs",
        type=str,
        metavar="<Genotype Storage>",
        dest="genotype_storage",
        help="Genotype Storage which will be used for import "
        "[default: %(default)s]",
        default=default_genotype_storage_id,
    )

    argv = parser.parse_args(argv)
    return argv


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    argv = parse_cli_arguments(argv, gpf_instance)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("impala").setLevel(logging.WARNING)

    genotype_storage_db = gpf_instance.genotype_storage_db
    genotype_storage = genotype_storage_db.get_genotype_storage(
        argv.genotype_storage
    )
    if not genotype_storage or (
        genotype_storage and not genotype_storage.is_impala()
    ):
        logger.error("missing or non-impala genotype storage")
        return

    partition_descriptor = None
    if argv.variants and os.path.exists(argv.variants):
        partition_config_file = os.path.join(
            argv.variants, "_PARTITION_DESCRIPTION")

        if os.path.isdir(argv.variants) and \
                os.path.exists(partition_config_file):
            partition_descriptor = ParquetPartitionDescriptor.from_config(
                partition_config_file, root_dirname=argv.variants
            )

    if partition_descriptor is None:
        partition_descriptor = NoPartitionDescriptor(
            root_dirname=argv.variants)

    genotype_storage.hdfs_upload_dataset(
        argv.study_id, argv.variants, argv.pedigree, partition_descriptor)


if __name__ == "__main__":
    main(sys.argv[1:])
