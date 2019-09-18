#!/usr/bin/env python
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance


def main(gpf_instance=None, argv=None):
    description = 'Generate genovo gene sets tool'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '--show-studies', help='This option will print available '
        'datasets and studies names', default=False,
        action='store_true')
    parser.add_argument(
        '--studies', help='Specify datasets and studies '
        'names for generating denovo gene sets. Default to all.',
        default=None, action='store')

    args = parser.parse_args(argv)

    if gpf_instance is None:
        gpf_instance = GPFInstance()
    dgsf = gpf_instance.denovo_gene_set_facade

    if args.show_studies:
        for study_id in dgsf.get_all_denovo_gene_set_ids():
            print(study_id)
    else:
        filter_studies_ids = None
        if args.studies:
            studies = args.studies.split(',')
            filter_studies_ids = [
                study_id
                for study_id in dgsf.get_all_denovo_gene_set_ids()
                if study_id in studies
            ]

        dgsf.build_cache(filter_studies_ids)


if __name__ == '__main__':
    main()
