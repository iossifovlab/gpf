#!/usr/bin/env python

import os
import sys
import argparse
import time
from copy import deepcopy

from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb

from tools.simple_study_import import impala_load_study


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='loading study parquet files in impala db',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--study-ids', type=str,
        metavar='<study IDs>',
        dest="study_ids",
        help='list of study IDs to load [default: all study ids]'
    )

    parser.add_argument(
        '--parquet-directories', type=str,
        metavar='<parquet directories>',
        dest="parquet_directories",
        help='list of parquet directories corresponding to study IDs '
             '[default: `study_config_directory/study_id/study_id`]'
    )

    parser_args = parser.parse_args(argv)
    return parser_args


def main(study_ids=None, parquet_directories=None):
    dae_config = DAEConfig()
    variants_db = VariantsDb(dae_config)

    if study_ids is None:
        study_ids = variants_db.get_studies_ids()
    if parquet_directories is None:
        temp_study_ids = deepcopy(study_ids)
        study_ids = []
        parquet_directories = []
        for study_id in temp_study_ids:
            study_config = variants_db.get_study_config(study_id)

            if study_config.file_format != 'impala':
                continue
            study_ids.append(study_id)

            parquet_directory = os.path.join(
                study_config.work_dir, study_config.id, study_config.id)
            parquet_directories.append(parquet_directory)

    for study_id, parquet_directory in zip(study_ids, parquet_directories):
        print('Loading `{}` study in impala `{}` db'.format(
            study_id, dae_config.impala_db))
        start = time.time()
        impala_load_study(dae_config, study_id, parquet_directory)
        print("Loaded `{}` study in impala `{}` db for {:.2f} sec".format(
            study_id, dae_config.impala_db, time.time() - start),
            file=sys.stderr)


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])

    study_ids = None
    parquet_directories = None
    if argv.study_ids is not None:
        study_ids = argv.study_ids.split(',')
        if argv.parquet_directories is not None:
            parquet_directories = argv.parquet_directories.split(',')

    main(study_ids=study_ids, parquet_directories=parquet_directories)
