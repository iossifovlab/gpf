#!/usr/bin/env python

'''
Created on Jun 4, 2018

@author: lubo
'''
from __future__ import print_function

import os
import sys
import argparse

from configurable_entities.configuration import DAEConfig

from backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator

from backends.configure import Configure
from backends.vcf.raw_vcf import RawFamilyVariants
from cyvcf2 import VCF

from backends.import_commons import build_contig_regions, \
    contigs_makefile_generate
from backends.vcf.builder import get_genome
from backends.thrift.import_tools import annotation_pipeline_cli_options, \
    construct_import_annotation_pipeline, variants_iterator_to_parquet

# import multiprocessing
# import functools


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def create_vcf_variants(config, region=None):

    freq_annotator = VcfAlleleFrequencyAnnotator()

    fvars = RawFamilyVariants(
        config=config, annotator=freq_annotator,
        region=region)
    return fvars


def import_vcf(dae_config, argv, defaults={}):
    assert os.path.exists(argv.vcf)
    assert os.path.exists(argv.pedigree)

    vcf_filename = argv.vcf
    ped_filename = argv.pedigree

    vcf_config = Configure.from_dict({
            'vcf': {
                'pedigree': ped_filename,
                'vcf': vcf_filename,
                'annotation': None,
            },
        })

    region = argv.region
    fvars = create_vcf_variants(vcf_config, region)

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv, defaults=defaults)

    variants_iterator_to_parquet(
        fvars,
        argv.output,
        argv.bucket_index,
        annotation_pipeline
    )


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert VCF file to parquet',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='vcf import or make generation for vcf import')

    parse_vcf_arguments(dae_config, subparsers)
    parser_make_arguments(dae_config, subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


def parser_common_arguments(dae_config, parser):
    options = annotation_pipeline_cli_options(dae_config)

    for name, args in options:
        parser.add_argument(name, **args)

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
    parser.add_argument(
        '-o', '--out', type=str, default='.',
        dest='output', metavar='<output filepath prefix>',
        help='output filepath prefix. '
        'If none specified, current directory is used [default: %(default)s]'
    )


def parse_vcf_arguments(dae_config, subparsers):
    parser = subparsers.add_parser('vcf')
    parser_common_arguments(dae_config, parser)

    parser.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert [default: %(default)s]'
    )

    parser.add_argument(
        '-b', '--bucket-index', type=int, default=1,
        dest='bucket_index', metavar='bucket index',
        help='bucket index [default: %(default)s]'
    )


def parser_make_arguments(dae_config, subparsers):
    parser = subparsers.add_parser('make')
    parser_common_arguments(dae_config, parser)

    parser.add_argument(
        '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len> '
        '[default: %(default)s]'
    )


def generate_makefile(dae_config, argv):
    assert os.path.exists(argv.vcf)
    assert os.path.exists(argv.pedigree)

    vcf_filename = argv.vcf
    ped_filename = argv.pedigree

    genome = get_genome(genome_file=None)
    data_contigs = get_contigs(vcf_filename)
    build_contigs = build_contig_regions(genome, argv.len)

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.output,
        "vcf2parquet.py vcf",
        argv.annotation_config,
        "{} {}".format(ped_filename, vcf_filename)
    )


if __name__ == "__main__":
    dae_config = DAEConfig()
    argv = parse_cli_arguments(dae_config, sys.argv[1:])

    if argv.type == 'vcf':
        import_vcf(dae_config, argv, defaults=dae_config.annotation_defaults)
    elif argv.type == 'make':
        generate_makefile(dae_config, argv)
