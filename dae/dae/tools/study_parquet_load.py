#!/usr/bin/env python
import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance


def parse_cli_arguments(argv, gpf_instance):
    parser = argparse.ArgumentParser(
        description='loading study parquet files in impala db',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'study_id', type=str,
        metavar='<study ID>',
        dest='study_id',
        help='study ID to be loaded'
    )

    parser.add_argument(
        'pedigree',
        type=str,
        metavar='<Pedigree Filepath>',
        dest='pedigree_file',
        help='path to the pedigree file'
    )

    parser.add_argument(
        'variants', type=str,
        metavar='<Variants Parquet Directory>',
        dest='variants_directory',
        help='path to directory which contains variants parquet data files'
    )

    default_genotype_storage_id = \
        gpf_instance.dae_config.\
        get('genotype_storage', {}).\
        get('default', None)

    parser.add_argument(
        '--genotype-storage', type=str,
        metavar='<Genotype Storage>',
        dest='genotype_storage',
        help='Genotype Storage which will be used for import '
             '[default: %(default)s]',
        default=default_genotype_storage_id,
    )

    parser.add_argument(
        '--partition-description', '--pd',
        type=str, default=None,
        metavar='<Partition Description Filepath>',
        dest='partition_description',
        help='path to the partition description file'
    )

    argv = parser.parse_args(argv)
    return argv


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config

    argv = parse_cli_arguments(dae_config, argv)

    genotype_storage_db = gpf_instance.genotype_storage_db
    genotype_storage = genotype_storage_db.get_genotype_storage(
        argv.genotype_storage
    )
    if not genotype_storage or \
            (genotype_storage and not genotype_storage.is_impala()):
        print('missing or non-impala genotype storage')
        return

    assert os.path.exists(argv.variants)
    if os.path.isdir(argv.variants):
        genotype_storage.impala_load_dataset(
            argv.study_id, argv.variants, argv.pedigree
        )
    else:
        genotype_storage.impala_load_study(
            argv.study_id, [argv.variants], [argv.pedigree]
        )


if __name__ == '__main__':
    main()
