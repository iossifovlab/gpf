#!/usr/bin/env python
import argparse

from studies.factory import VariantsDb
from configurable_entities.configuration import DAEConfig

from common_reports.common_report import CommonReportsGenerator
from common_reports.config import CommonReportsQueryObjects


def main(dae_config=None):
    description = 'Generate common reports tool'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '--show_query_objects', help='This option will print available query '
        'objects (datasets and studies) names', default=False,
        action='store_true')
    parser.add_argument(
        '--query_objects', help='Specify query objects (datasets and studies) '
        'names for generating common report. Default to all query objects.',
        default=None, action='store')

    args = parser.parse_args()

    dae_config = DAEConfig()
    vdb = VariantsDb(dae_config)
    common_reports_query_objects = CommonReportsQueryObjects(
        vdb.study_facade, vdb.dataset_facade)

    if args.show_query_objects:
        for query_object in\
                common_reports_query_objects.query_objects_with_config.keys():
            print(query_object.name)
    else:
        if args.query_objects:
            query_objects = args.query_objects.split(',')
            common_reports_query_objects.filter_query_objects(query_objects)

        crg = CommonReportsGenerator(common_reports_query_objects)
        crg.save_common_reports()


if __name__ == '__main__':
    main()
