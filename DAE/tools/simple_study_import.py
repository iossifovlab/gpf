#!/usr/bin/env python

from __future__ import print_function, absolute_import

import os
import sys
import argparse

from configurable_entities.configuration import DAEConfig
from tools.vcf2parquet import import_vcf
from tools.dae2parquet import import_dae_denovo


def parse_common_arguments(dae_config, parser):
    parser.add_argument(
        'id', type=str,
        metavar='<study ID>',
        help='unique study ID to use'
    )
    parser.add_argument(
        '-o', '--out', type=str, default='data/',
        dest='output', metavar='<output directory>',
        help='output directory. '
        'If none specified, "data/" directory is used [default: %(default)s]'
    )

def parse_vcf_arguments(dae_config, subparsers):
    parser = subparsers.add_parser('vcf')

    parse_common_arguments(dae_config, parser)

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        'vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )

def parse_dae_denovo_arguments(dae_config, subparsers):
    parser = subparsers.add_parser('denovo')

    parse_common_arguments(dae_config, parser)

    parser.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )

    parser.add_argument(
        'variants', type=str,
        metavar='<variants filename>',
        help='DAE denovo variants file'
    )

    parser.add_argument(
        '-f', '--family-format', type=str,
        default='pedigree',
        dest='family_format',
        help='families file format - `pedigree` or `simple`; '
        '[default: %(default)s]'
    )


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='simple import of new study data',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='vcf import or DAE denovo import')

    parse_vcf_arguments(dae_config, subparsers)
    parse_dae_denovo_arguments(dae_config, subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


STUDY_CONFIG_TEMPLATE = """
[study]

id = {id}
prefix = {output}

"""

def generate_study_config(dae_config, argv):
    assert argv.id is not None
    assert argv.output is not None

    dirname = os.getcwd()
    filename = os.path.join(dirname, "{}.conf".format(argv.id))

    if os.path.exists(filename):
        print("configuration file already exists:", filename)
        print("skipping generation of default config for:", argv.id)
        return

    with open(filename, 'w') as outfile:
        outfile.write(STUDY_CONFIG_TEMPLATE.format(
            id=argv.id,
            output=argv.output
        ))

def generate_common_report(dae_config, study_id):
    from tools.generate_common_report import main
    argv = ['--studies', study_id]
    main(dae_config, argv)


if __name__ == "__main__":
    dae_config = DAEConfig()
    argv = parse_cli_arguments(dae_config, sys.argv[1:])
    study_id = argv.id

    os.makedirs(argv.output, exist_ok=True)

    if argv.type == 'vcf':
        import_vcf(
            dae_config, argv, defaults=dae_config.annotation_defaults)
    elif argv.type == 'denovo':
        import_dae_denovo(
            dae_config, argv, defaults=dae_config.annotation_defaults)
    else:
        raise ValueError("unexpected subcommand")

    generate_study_config(dae_config, argv)
    generate_common_report(dae_config, study_id)

