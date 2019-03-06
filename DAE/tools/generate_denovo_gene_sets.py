#!/usr/bin/env python
import argparse

from configurable_entities.configuration import DAEConfig
from gene.gene_set_collections import GeneSetsCollections
from studies.factory import VariantsDb


def main():
    description = 'Generate genovo gene sets tool'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '--show_query_objects', help='This option will print available query '
        'objects (datasets and studies) names', default=False,
        action='store_true')
    parser.add_argument(
        '--query_objects', help='Specify query objects (datasets and studies) '
        'names for generating denovo gene sets. Default to all query objects.',
        default=None, action='store')

    args = parser.parse_args()

    config = DAEConfig()
    variants_db = VariantsDb(config)
    gsc = GeneSetsCollections(variants_db.dataset_facade)
    denovo = gsc.get_gene_sets_collection('denovo', load=False)

    if args.show_query_objects:
        for query_object in denovo.get_study_groups():
            print(query_object.name)
    else:
        filter_query_objects_ids = None
        if args.query_objects:
            query_objects = args.query_objects.split(',')
            filter_query_objects_ids = [
                qo.id
                for qo in denovo.get_study_groups()
                if qo.name in query_objects
            ]

        denovo.build_cache(filter_query_objects_ids)


if __name__ == '__main__':
    main()
