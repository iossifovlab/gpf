#!/usr/bin/env python

'''
Created on Jul 23, 2018

@author: lubo
'''
import os
import sys

import pysam
import argparse

from dae.configurable_entities.configuration import DAEConfig

from dae.annotation.tools.file_io_parquet import ParquetSchema

from dae.backends.vcf.builder import get_genome
from dae.backends.configure import Configure
from dae.backends.dae.raw_dae import RawDAE, RawDenovo

from dae.backends.import_commons import build_contig_regions, \
    contigs_makefile_generate

from dae.backends.import_commons import annotation_pipeline_cli_options, \
    construct_import_annotation_pipeline

from dae.backends.impala.import_tools import variants_iterator_to_parquet


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:
        return tbx.contigs


def dae_build_transmitted(
        dae_config, annotation_pipeline, argv, defaults={},
        study_id=None, filesystem=None):

    config = Configure.from_dict({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    assert argv.output is not None
    genome = get_genome(genome_file=None)

    fvars = RawDAE(
        config.dae.summary_filename,
        config.dae.toomany_filename,
        config.dae.family_filename,
        region=argv.region,
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

    annotation_schema = ParquetSchema()
    annotation_pipeline.collect_annotator_schema(annotation_schema)

    impala_config = Configure.from_prefix_impala(
        argv.output, bucket_index=argv.bucket_index,
        db=None, study_id=study_id).impala

    variants_iterator_to_parquet(
        fvars,
        impala_config,
        bucket_index=argv.bucket_index,
        rows=argv.rows,
        annotation_pipeline=annotation_pipeline,
        filesystem=filesystem,
        no_reference=argv.no_reference
    )


def dae_build_makefile(dae_config, argv):
    data_contigs = get_contigs(argv.summary)
    genome = get_genome(genome_file=None)
    build_contigs = build_contig_regions(genome, argv.len)

    family_format = ""
    if argv.family_format == 'simple':
        family_format = "-f simple"
    elif argv.family_format == 'pedigree':
        family_format = "-f simple"
    else:
        raise ValueError("unexpected family format: {}".format(
            argv.family_format
        ))
    no_reference = ""
    if argv.no_reference:
        no_reference = "--no-reference"

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.output,
        'dae2parquet.py dae {family_format} {no_reference}'.format(
            family_format=family_format,
            no_reference=no_reference),
        argv.annotation_config,
        "{family_filename} {summary_filename} {toomany_filename}".format(
            family_filename=argv.families,
            summary_filename=argv.summary,
            toomany_filename=argv.toomany),
        rows=argv.rows,
        log_directory=argv.log
    )


def import_dae_denovo(
        dae_config, annotation_pipeline,
        families_filename, variants_filename,
        family_format='pedigree', output='.', rows=10000,
        bucket_index=0, defaults={}, study_id=None, filesystem=None):

    config = Configure.from_dict({
        "denovo": {
            'denovo_filename': variants_filename,
            'family_filename': families_filename
        }})

    genome = get_genome()
    fvars = RawDenovo(
        config.denovo.denovo_filename,
        config.denovo.family_filename,
        genome=genome,
        annotator=annotation_pipeline)
    if family_format == 'simple':
        fvars.load_simple_families()
    elif family_format == 'pedigree':
        fvars.load_pedigree_families()
    else:
        raise ValueError("unexpected family format: {}".format(
            family_format
        ))

    df = fvars.load_denovo_variants()
    assert df is not None

    assert output is not None

    if study_id is None:
        filename = os.path.basename(families_filename)
        study_id = os.path.splitext(filename)[0]
        print(filename, os.path.splitext(filename), study_id)

    impala_config = Configure.from_prefix_impala(
        output, bucket_index=bucket_index, db=None, study_id=study_id).impala
    print("converting into ", impala_config, file=sys.stderr)

    return variants_iterator_to_parquet(
        fvars,
        impala_config,
        bucket_index=bucket_index,
        rows=rows,
        annotation_pipeline=annotation_pipeline,
        filesystem=filesystem
    )


def init_parser_dae_common(dae_config, parser):
    parser.add_argument(
        'families', type=str,
        metavar='<families filename>',
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

    parser.add_argument(
        '--no-reference', action="store_true", default=None,
        help="Skip reference alleles and all unknown alleles"
    )

    parser.add_argument(
        '-r', '--rows', type=int,
        default=100000,
        dest='rows', metavar='rows',
        help='row group size'
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

    parser.add_argument(
        '--log', type=str,
        default=None,
        dest='log', metavar='<log dir>',
        help='directory to store log files'
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
    dae_config = DAEConfig.make_config()

    argv = parse_cli_arguments(dae_config, sys.argv[1:])
    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv)

    if argv.type == 'denovo':
        import_dae_denovo(
            dae_config, annotation_pipeline,
            argv.families, argv.variants,
            family_format=argv.family_format,
            output=argv.output,
            rows=argv.rows, bucket_index=0
        )
    elif argv.type == 'dae':
        dae_build_transmitted(
            dae_config, annotation_pipeline, argv,
            defaults=dae_config.annotation_defaults)
    elif argv.type == 'make':
        dae_build_makefile(dae_config, argv)
