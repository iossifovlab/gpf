#!/usr/bin/env python

import sys
import argparse
import logging

from dae.impala_storage.schema1.import_commons import DatasetHelpers
from dae.gpf_instance.gpf_instance import GPFInstance


def main(argv, gpf_instance=None):
    """Entry point for the genotype data tool."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", "-V", action="count", default=0)

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true", default=None)

    parser.add_argument(
        "--source-id",
        type=str,
        default=None,
        dest="source_id",
        metavar="<source study id>",
        help="Source study ID. "
    )

    parser.add_argument(
        "--dest-id",
        type=str,
        default=None,
        dest="dest_id",
        metavar="<dest study id>",
        help="Destination study ID. "
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

    logging.getLogger("impala.hiveserver2").setLevel(logging.ERROR)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    assert argv.source_id is not None
    assert argv.dest_id is not None

    assert argv.source_id in gpf_instance.get_genotype_data_ids()
    assert argv.dest_id in gpf_instance.get_genotype_data_ids()

    source_study = gpf_instance.get_genotype_data(argv.source_id)
    assert source_study is not None
    assert not source_study.is_group

    dest_study = gpf_instance.get_genotype_data(argv.dest_id)
    assert dest_study is not None
    assert not dest_study.is_group

    helpers = DatasetHelpers(gpf_instance)

    genotype_storage = helpers.get_genotype_storage(argv.source_id)

    assert helpers.check_dataset_hdfs_directories(
        genotype_storage, argv.source_id)
    assert helpers.check_dataset_hdfs_directories(
        genotype_storage, argv.dest_id)

    assert helpers.check_dataset_impala_tables(argv.source_id)
    assert helpers.check_dataset_impala_tables(argv.dest_id)

    helpers.dataset_drop_impala_tables(argv.dest_id, dry_run=argv.dry_run)
    helpers.dataset_remove_hdfs_directory(argv.dest_id, dry_run=argv.dry_run)
    helpers.dataset_rename_hdfs_directory(
        argv.source_id, argv.dest_id, dry_run=argv.dry_run)
    helpers.dataset_recreate_impala_tables(
        argv.source_id, argv.dest_id, dry_run=argv.dry_run)
    helpers.dataset_drop_impala_tables(argv.source_id, dry_run=argv.dry_run)
    helpers.disable_study_config(argv.source_id, dry_run=argv.dry_run)


if __name__ == "__main__":
    main(sys.argv[1:])
