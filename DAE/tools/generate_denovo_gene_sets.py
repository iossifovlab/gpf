#!/usr/bin/env python
import argparse

from configurable_entities.configuration import DAEConfig
from gene.gene_set_collections import GeneSetsCollections
from studies.factory import VariantsDb


def main(options=None):
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

    args = parser.parse_args(options)

    config = DAEConfig()
    variants_db = VariantsDb(config)
    gsc = GeneSetsCollections(variants_db)
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    if args.show_studies:
        for study_id in denovo.get_study_ids():
            print(study_id)
    else:
        filter_studies_ids = None
        if args.studies:
            studies = args.studies.split(',')
            filter_studies_ids = [
                study_id
                for study_id in denovo.get_study_ids()
                if study_id in studies
            ]

        denovo.build_cache(filter_studies_ids)


if __name__ == '__main__':
    main()
