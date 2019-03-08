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
    gsc = GeneSetsCollections(variants_db.dataset_facade)
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    if args.show_studies:
        for query_object in denovo.get_study_groups():
            print(query_object.id)
    else:
        filter_query_objects_ids = None
        if args.studies:
            query_objects = args.studies.split(',')
            filter_query_objects_ids = [
                qo.id
                for qo in denovo.get_study_groups()
                if qo.id in query_objects
            ]

        denovo.build_cache(filter_query_objects_ids)


if __name__ == '__main__':
    main()
