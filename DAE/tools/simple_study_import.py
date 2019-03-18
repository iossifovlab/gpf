#!/usr/bin/env python

from __future__ import print_function, absolute_import

import os
import sys
import argparse

from configurable_entities.configuration import DAEConfig
from backends.thrift.import_tools import construct_import_annotation_pipeline

from tools.vcf2parquet import import_vcf
from tools.dae2parquet import import_dae_denovo


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='simple import of new study data',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        '--id', type=str,
        metavar='<study ID>',
        dest="id",
        help='unique study ID to use'
    )

    parser.add_argument(
        '--vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )

    parser.add_argument(
        '--denovo', type=str,
        metavar='<de Novo variants filename>',
        help='DAE denovo variants file'
    )

    parser.add_argument(
        '-o', '--out', type=str, default='data/',
        dest='output', metavar='<output directory>',
        help='output directory. '
        'If none specified, "data/" directory is used [default: %(default)s]'
    )

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
    if argv.id is not None:
        study_id = argv.id
    else:
        study_id = os.path.basename(argv.pedigree)

    os.makedirs(argv.output, exist_ok=True)

    assert argv.vcf is not None or argv.denovo is not None

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv)

    if argv.vcf is not None:
        import_vcf(
            dae_config, annotation_pipeline, argv)
    elif argv.denovo is not None:
        import_dae_denovo(
            dae_config, annotation_pipeline,
            argv.pedigree, argv.denovo, family_format='pedigree', argv=argv)
    else:
        raise ValueError("at least VCF of De Novo variants file should be specified")

    # generate_study_config(dae_config, argv)
    # generate_common_report(dae_config, study_id)
