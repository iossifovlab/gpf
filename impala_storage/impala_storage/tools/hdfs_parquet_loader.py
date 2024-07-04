#!/usr/bin/env python
import argparse
import logging
import os
import sys

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.parquet.partition_descriptor import PartitionDescriptor

logger = logging.getLogger("hdfs_parquet_loader")


def parse_cli_arguments(
    argv: list[str], gpf_instance: GPFInstance,
) -> argparse.Namespace:
    """Configure and create CLI arguments parser."""
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--verbose", "-V", action="count", default=0)

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

    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Upload parquet dataset into HDFS storage."""
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    args = parse_cli_arguments(argv or sys.argv[1:], gpf_instance)

    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("impala").setLevel(logging.WARNING)

    genotype_storages = gpf_instance.genotype_storages
    genotype_storage = genotype_storages.get_genotype_storage(
        args.genotype_storage,
    )
    if not genotype_storage or \
            (genotype_storage
             and genotype_storage.storage_type != "impala"):
        logger.error("missing or non-impala genotype storage")
        return

    partition_descriptor = None
    if args.variants and os.path.exists(args.variants):
        partition_config_file = os.path.join(
            args.variants, "_PARTITION_DESCRIPTION")

        if os.path.isdir(args.variants) and \
                os.path.exists(partition_config_file):
            partition_descriptor = PartitionDescriptor.parse(
                partition_config_file)

    if partition_descriptor is None:
        partition_descriptor = PartitionDescriptor()

    genotype_storage.hdfs_upload_dataset(
        args.study_id, args.variants, args.pedigree, partition_descriptor)


if __name__ == "__main__":
    main(sys.argv[1:])
