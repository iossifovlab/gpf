#!/usr/bin/env python
import argparse

from studies.factory import VariantsDb
from configurable_entities.configuration import DAEConfig

from common_reports.common_report import CommonReportsGenerator
from common_reports.config import CommonReportsStudies


def main(dae_config=None, argv=None):
    description = 'Generate common reports tool'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '--show-studies', help='This option will print available '
        'datasets and studies names', default=False,
        action='store_true')
    parser.add_argument(
        '--studies', help='Specify datasets and studies '
        'names for generating common report. Default to all query objects.',
        default=None, action='store')

    args = parser.parse_args(argv)

    if dae_config is None:
        dae_config = DAEConfig()

    vdb = VariantsDb(dae_config)
    common_reports_query_objects = CommonReportsStudies(
        vdb.study_facade, vdb.dataset_facade)

    if args.show_studies:
        for query_object in\
                common_reports_query_objects.studies_with_config.keys():
            print(query_object.id)
    else:
        if args.studies:
            query_objects = args.studies.split(',')
            common_reports_query_objects.filter_studies(query_objects)

        crg = CommonReportsGenerator(common_reports_query_objects)
        crg.save_common_reports()


if __name__ == '__main__':
    main()
