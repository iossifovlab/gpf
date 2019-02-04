#!/usr/bin/env python

'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function
import sys
import time

import pysam
import argparse

from backends.vcf.builder import get_genome
from backends.configure import Configure
from backends.thrift.raw_dae import RawDAE, RawDenovo

from backends.thrift.parquet_io import save_ped_df_to_parquet, \
    VariantsParquetWriter
from backends.import_commons import build_contig_regions, \
    contigs_makefile_generate


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:  # @UndefinedVariable
        return tbx.contigs


def dae_build_region(argv):
    config = Configure.from_dict({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    # contigs = ['chr21', 'chr22']

    assert argv.out is not None
    parquet_config = Configure.from_prefix_parquet(argv.out).parquet

    genome = get_genome(genome_file=None)

    dae = RawDAE(
        config.dae.summary_filename,
        config.dae.toomany_filename,
        config.dae.family_filename,
        region=argv.region,
        genome=genome,
        annotator=None)

    dae.load_families()

    save_ped_df_to_parquet(
        dae.ped_df,
        parquet_config.pedigree)

    print("going to build: ", argv.region)
    start = time.time()
    variants_writer = VariantsParquetWriter(dae.full_variants_iterator())
    variants_writer.save_variants_to_parquet(
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=argv.bucket_index)
    end = time.time()

    print("DONE region: {} for {} sec".format(
        argv.region, round(end-start)))


def dae_build_makefile(argv):
    data_contigs = get_contigs(argv.summary)
    genome = get_genome(genome_file=None)
    build_contigs = build_contig_regions(genome, argv.len)

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.out,
        'dae2parquet.py dae',
        "{family_filename} {summary_filename} {toomany_filename}".format(
            family_filename=argv.families,
            summary_filename=argv.summary,
            toomany_filename=argv.toomany)
    )


def denovo_build(argv):
    config = Configure.from_dict({
        "denovo": {
            'denovo_filename': argv.variants,
            'family_filename': argv.families
        }})

    genome = get_genome()

    denovo = RawDenovo(
        config.denovo.denovo_filename,
        config.denovo.family_filename,
        genome=genome,
        annotator=None)

    denovo.load_families()
    df = denovo.load_denovo_variants()
    assert df is not None

    assert argv.out is not None
    parquet_config = Configure.from_prefix_parquet(argv.out).parquet
    save_ped_df_to_parquet(
        denovo.ped_df,
        parquet_config.pedigree)

    print("going to build: ", config.denovo)
    start = time.time()

    variants_writer = VariantsParquetWriter(denovo.full_variants_iterator())
    variants_writer.save_variants_to_parquet(
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=argv.bucket_index)
    end = time.time()

    print("DONE region: {} for {} sec".format(
        config.denovo, round(end-start)))


def init_parser_denovo(subparsers):
    parser_denovo = subparsers.add_parser('denovo')

    parser_denovo.add_argument(
        'variants', type=str,
        metavar='<variants filename>',
        help='annotated variants file'
    )
    parser_denovo.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser_denovo.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )
    parser_denovo.add_argument(
        '-b', '--bucket-index', type=int,
        default=0,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )


def init_transmitted_common(parser):
    parser.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
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
    parser.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )


def init_parser_dae(subparsers):
    parser_dae = subparsers.add_parser('dae')

    init_transmitted_common(parser_dae)

    parser_dae.add_argument(
        '-p', '--processes', type=int, default=4,
        dest='processes_count', metavar='processes count',
        help='number of processes'
    )

    parser_dae.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert'
    )

    parser_dae.add_argument(
        '-b', '--bucket-index', type=int,
        default=1,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )


def init_parser_make(subparsers):
    parser_region = subparsers.add_parser('make')

    init_transmitted_common(parser_region)

    parser_region.add_argument(
        '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len>'
    )


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert DAE file to parquet')

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='denovo or transmitted study')

    init_parser_denovo(subparsers)
    init_parser_dae(subparsers)
    init_parser_make(subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])

    if argv.type == 'denovo':
        denovo_build(argv)
    elif argv.type == 'dae':
        dae_build_region(argv)
    elif argv.type == 'make':
        dae_build_makefile(argv)
