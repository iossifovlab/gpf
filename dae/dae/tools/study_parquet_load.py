#!/usr/bin/env python

import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.storage.genotype_storage_factory import \
    GenotypeStorageFactory


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    default_genotype_storage_id = \
        dae_config.get('genotype_storage', {}).get('default', None)

    parser = argparse.ArgumentParser(
        description='loading study parquet files in impala db',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--study-id', type=str,
        metavar='<study ID>',
        dest='study_id',
        help='study ID to be load'
    )

    parser.add_argument(
        '--genotype-storage', type=str,
        metavar='<Genotype Storage>',
        dest='genotype_storage',
        help='Genotype Storage which will be used for import '
             '[default: %(default)s]',
        default=default_genotype_storage_id,
    )

    parser.add_argument(
        '--pedigree-directory', type=str,
        metavar='<Pedigree Parquet Directory>',
        dest='pedigree_directory',
        help='path to directory which contains pedigree parquet data files'
    )

    parser.add_argument(
        '--variants-directory', type=str,
        metavar='<Variants Parquet Directory>',
        dest='variants_directory',
        help='path to directory which contains variants parquet data files'
    )

    parser_args = parser.parse_args(argv)
    return parser_args


def main(gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config

    argv = parse_cli_arguments(dae_config, sys.argv[1:])

    if argv.study_id is None or argv.pedigree_directory is None or \
            argv.variants_directory is None:
        return

    genotype_storage_factory = GenotypeStorageFactory(dae_config)
    genotype_storage = genotype_storage_factory.get_genotype_storage(
        argv.genotype_storage
    )
    if not genotype_storage or \
            (genotype_storage and not genotype_storage.is_impala()):
        return

    genotype_storage.impala_load_study(
        argv.study_id, [argv.variants_directory], [argv.pedigree_directory]
    )


if __name__ == '__main__':
    main()
