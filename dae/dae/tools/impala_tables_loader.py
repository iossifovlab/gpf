#!/usr/bin/env python
import os
import sys
import argparse
import logging

import toml

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.parquet.schema1.parquet_io import NoPartitionDescriptor, \
    ParquetPartitionDescriptor


logger = logging.getLogger(__name__)


def parse_cli_arguments(argv, gpf_instance):
    """Configure and create a CLI arguments parser."""
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
        "--pedigree",
        type=str,
        metavar="<Pedigree Filepath>",
        help="HDFS path to the pedigree file",
    )

    parser.add_argument(
        "--variants",
        type=str,
        metavar="<Variants Parquet Directory>",
        help="HDFS path to directory which contains variants parquet files",
    )

    parser.add_argument(
        "--variants-sample",
        type=str,
        metavar="<Variants sample HDFS file>",
        dest="variants_sample",
        help="Variants sample HDFS parquet file name",
        default=None,
    )

    parser.add_argument(
        "--variants-schema",
        type=str,
        metavar="<Variants Schema description file>",
        dest="variants_schema",
        help="Variants schema description file name",
        default=None,
    )

    parser.add_argument(
        "--partition-description",
        "--pd",
        type=str,
        metavar="<Partition Description>",
        dest="partition_description",
        help="Partition description file name",
        default=None,
    )

    default_genotype_storage_id = (
        gpf_instance.dae_config.genotype_storage.default)

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


def main(argv=None, gpf_instance=None):
    """Import parquet dataset into Impala genotype storage."""
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    argv = parse_cli_arguments(argv or sys.argv[1:], gpf_instance)

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
        argv.genotype_storage)

    if not genotype_storage or \
            genotype_storage.get_storage_type() != "impala":
        logger.error("missing or non-impala genotype storage")
        return

    study_id = argv.study_id

    if argv.variants is not None:
        hdfs_variants_dir = argv.variants
    elif argv.variants_sample or argv.variants_schema:
        hdfs_variants_dir = \
            genotype_storage.default_variants_hdfs_dirname(study_id)
        # if not genotype_storage.hdfs_helpers.exists(hdfs_variants_dir):
        #     hdfs_variants_dir = None
    else:
        hdfs_variants_dir = None

    if argv.pedigree is not None:
        hdfs_pedigree_file = argv.pedigree
    else:
        hdfs_pedigree_file = \
            genotype_storage.default_pedigree_hdfs_filename(study_id)

    logger.info("HDFS variants dir: %s", hdfs_variants_dir)
    logger.info("HDFS pedigree file: %s", hdfs_pedigree_file)

    partition_config_file = None
    if argv.partition_description is not None:
        partition_config_file = argv.partition_description
        assert os.path.isfile(partition_config_file), partition_config_file
    logger.info("partition_config_file: %s", partition_config_file)

    if partition_config_file is not None and \
            os.path.isfile(partition_config_file):
        partition_description = ParquetPartitionDescriptor.from_config(
            partition_config_file)
    else:
        partition_description = NoPartitionDescriptor()

    variants_schema = None
    if argv.variants_schema is not None:
        assert os.path.exists(argv.variants_schema), argv.variants_schema
        assert os.path.isfile(argv.variants_schema), argv.variants_schema
        with open(argv.variants_schema) as infile:
            content = infile.read()
            schema = toml.loads(content)
            variants_schema = schema["variants_schema"]

    genotype_storage.impala_import_dataset(
        argv.study_id,
        hdfs_pedigree_file,
        hdfs_variants_dir,
        partition_description=partition_description,
        variants_sample=argv.variants_sample,
        variants_schema=variants_schema)


if __name__ == "__main__":
    main(sys.argv[1:])
