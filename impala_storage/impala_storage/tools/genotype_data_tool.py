#!/usr/bin/env python

import argparse
import logging
import sys
from typing import Optional

from dae.gpf_instance.gpf_instance import GPFInstance
from impala_storage.schema1.impala_dataset_helpers import ImpalaDatasetHelpers


def main(
    argv: list[str],
    gpf_instance: Optional[GPFInstance] = None,
) -> None:
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
        help="Source study ID. ",
    )

    parser.add_argument(
        "--dest-id",
        type=str,
        default=None,
        dest="dest_id",
        metavar="<dest study id>",
        help="Destination study ID. ",
    )

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("impala.hiveserver2").setLevel(logging.ERROR)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    assert args.source_id is not None
    assert args.dest_id is not None

    assert args.source_id in gpf_instance.get_genotype_data_ids()
    assert args.dest_id in gpf_instance.get_genotype_data_ids()

    source_study = gpf_instance.get_genotype_data(args.source_id)
    assert source_study is not None
    assert not source_study.is_group

    dest_study = gpf_instance.get_genotype_data(args.dest_id)
    assert dest_study is not None
    assert not dest_study.is_group

    helpers = ImpalaDatasetHelpers(gpf_instance)

    genotype_storage = helpers.get_genotype_storage(args.source_id)

    assert helpers.check_dataset_hdfs_directories(
        genotype_storage, args.source_id)
    assert helpers.check_dataset_hdfs_directories(
        genotype_storage, args.dest_id)

    assert helpers.check_dataset_impala_tables(args.source_id)
    assert helpers.check_dataset_impala_tables(args.dest_id)

    helpers.dataset_drop_impala_tables(args.dest_id, dry_run=args.dry_run)
    helpers.dataset_remove_hdfs_directory(args.dest_id, dry_run=args.dry_run)
    helpers.dataset_rename_hdfs_directory(
        args.source_id, args.dest_id, dry_run=args.dry_run)
    helpers.dataset_recreate_impala_tables(
        args.source_id, args.dest_id, dry_run=args.dry_run)
    helpers.dataset_drop_impala_tables(args.source_id, dry_run=args.dry_run)
    helpers.disable_study_config(args.source_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main(sys.argv[1:])
