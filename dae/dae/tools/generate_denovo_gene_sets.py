#!/usr/bin/env python
import argparse

from dae.configuration.dae_config_parser import DAEConfigParser
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade
from dae.studies.variants_db import VariantsDb


def main(dae_config=None, argv=None):
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

    if dae_config is None:
        dae_config = DAEConfigParser.read_and_parse_file_configuration()
    variants_db = VariantsDb(dae_config)

    dgsf = DenovoGeneSetFacade(variants_db)

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
