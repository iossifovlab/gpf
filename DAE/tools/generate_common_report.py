#!/usr/bin/env python
import argparse

from studies.factory import VariantsDb
from configurable_entities.configuration import DAEConfig

from common_reports.common_report_facade import CommonReportFacade


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
    common_report_facade = CommonReportFacade(vdb)

    if args.show_studies:
        for study_id in common_report_facade.get_all_common_report_ids():
            print(study_id)
    else:
        if args.studies:
            studies = args.studies.split(',')
            common_report_facade.generate_common_reports(studies)
        else:
            common_report_facade.generate_all_common_reports()


if __name__ == '__main__':
    main()
