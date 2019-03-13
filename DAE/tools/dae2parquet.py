#!/usr/bin/env python

'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function
import sys

import pysam
import argparse

from configurable_entities.configuration import DAEConfig

from backends.vcf.builder import get_genome
from backends.configure import Configure
from backends.thrift.raw_dae import RawDAE, RawDenovo

from backends.import_commons import build_contig_regions, \
    contigs_makefile_generate

from backends.thrift.import_tools import annotation_pipeline_cli_options, \
    construct_import_annotation_pipeline, variants_iterator_to_parquet


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:  # @UndefinedVariable
        return tbx.contigs


def dae_build_transmitted(dae_config, argv, defaults={}):
    config = Configure.from_dict({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    # contigs = ['chr21', 'chr22']

    assert argv.output is not None
    genome = get_genome(genome_file=None)

    fvars = RawDAE(
        config.dae.summary_filename,
        config.dae.toomany_filename,
        config.dae.family_filename,
        region=argv.region,
        genome=genome)

    if argv.family_format == 'simple':
        fvars.load_simple_families()
    elif argv.family_format == 'pedigree':
        fvars.load_pedigree_families()
    else:
        raise ValueError("unexpected family format: {}".format(
            argv.family_format
        ))

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv, defaults=defaults)

    variants_iterator_to_parquet(
        fvars,
        argv.output,
        argv.bucket_index,
        annotation_pipeline
    )


def dae_build_makefile(dae_config, argv):
    data_contigs = get_contigs(argv.summary)
    genome = get_genome(genome_file=None)
    build_contigs = build_contig_regions(genome, argv.len)

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.output,
        'dae2parquet.py dae',
        argv.annotation_config,
        "{family_filename} {summary_filename} {toomany_filename}".format(
            family_filename=argv.families,
            summary_filename=argv.summary,
            toomany_filename=argv.toomany)
    )


def import_dae_denovo(dae_config, argv, defaults={}):
    config = Configure.from_dict({
        "denovo": {
            'denovo_filename': argv.variants,
            'family_filename': argv.families
        }})

    genome = get_genome()
    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv, defaults=defaults)

    fvars = RawDenovo(
        config.denovo.denovo_filename,
        config.denovo.family_filename,
        genome=genome,
        annotator=annotation_pipeline)
    if argv.family_format == 'simple':
        fvars.load_simple_families()
    elif argv.family_format == 'pedigree':
        fvars.load_pedigree_families()
    else:
        raise ValueError("unexpected family format: {}".format(
            argv.family_format
        ))

    df = fvars.load_denovo_variants()
    assert df is not None

    assert argv.output is not None

    variants_iterator_to_parquet(
        fvars,
        argv.output,
        argv.bucket_index,
        annotation_pipeline=annotation_pipeline
    )


def init_parser_dae_common(dae_config, parser):
    parser.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )

    options = annotation_pipeline_cli_options(dae_config)
    for name, args in options:
        parser.add_argument(name, **args)

    parser.add_argument(
        '-o', '--out', type=str, default='./',
        dest='output', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )
    parser.add_argument(
        '-b', '--bucket-index', type=int,
        default=0,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )
    parser.add_argument(
        '-f', '--family-format', type=str,
        default='pedigree',
        dest='family_format',
        help='families file format - `pedigree` or `simple`; '
        '[default: %(default)s]'
    )


def init_parser_denovo(dae_config, subparsers):
    parser_denovo = subparsers.add_parser('denovo')
    init_parser_dae_common(dae_config, parser_denovo)

    parser_denovo.add_argument(
        'variants', type=str,
        metavar='<variants filename>',
        help='DAE denovo variants file'
    )


def init_transmitted_common(dae_config, parser):

    init_parser_dae_common(dae_config, parser)

    parser.add_argument(
        'summary', type=str,
        metavar='<summary filename>',
        help=''
    )
    parser.add_argument(
        'toomany', type=str,
        metavar='<toomany filename>',
        help=''
    )


def init_parser_dae(dae_config, subparsers):
    parser_dae = subparsers.add_parser('dae')

    init_transmitted_common(dae_config, parser_dae)

    parser_dae.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert'
    )


def init_parser_make(dae_config, subparsers):
    parser = subparsers.add_parser('make')

    init_transmitted_common(dae_config, parser)

    parser.add_argument(
        '-l', '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len>'
    )


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert DAE file to parquet')

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='denovo or transmitted study')

    init_parser_denovo(dae_config, subparsers)
    init_parser_dae(dae_config, subparsers)
    init_parser_make(dae_config, subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


if __name__ == "__main__":
    dae_config = DAEConfig()

    argv = parse_cli_arguments(dae_config, sys.argv[1:])

    if argv.type == 'denovo':
        import_dae_denovo(
            dae_config, argv, defaults=dae_config.annotation_defaults)
    elif argv.type == 'dae':
        dae_build_transmitted(
            dae_config, argv, defaults=dae_config.annotation_defaults)
    elif argv.type == 'make':
        dae_build_makefile(dae_config, argv)
