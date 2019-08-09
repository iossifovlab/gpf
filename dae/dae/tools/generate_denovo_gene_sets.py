#!/usr/bin/env python
import argparse

from dae.configuration.configuration import DAEConfig
from dae.gene.denovo_gene_set_collection_facade import \
    DenovoGeneSetCollectionFacade
from dae.studies.factory import VariantsDb


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

    config = DAEConfig.make_config()
    variants_db = VariantsDb(config)
    dgscf = DenovoGeneSetCollectionFacade(variants_db)

    if args.show_studies:
        for study_id in dgscf.get_all_denovo_gene_set_ids():
            print(study_id)
    else:
        filter_studies_ids = None
        if args.studies:
            studies = args.studies.split(',')
            filter_studies_ids = [
                study_id
                for study_id in dgscf.get_all_denovo_gene_set_ids()
                if study_id in studies
            ]

        dgscf.build_cache(filter_studies_ids)


if __name__ == '__main__':
    main()
