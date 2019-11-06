#!/usr/bin/env python

import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.annotation.tools.annotator_config import annotation_config_cli_options

from dae.backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator

from dae.backends.configure import Configure
from dae.backends.vcf.raw_vcf import RawVcfVariants
from cyvcf2 import VCF

from dae.backends.import_commons import build_contig_regions, \
    contigs_makefile_generate
from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.backends.impala.import_tools import variants_iterator_to_parquet

# import multiprocessing
# import functools


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def import_vcf(
        dae_config, genomes_db, annotation_pipeline,
        pedigree_df, vcf_filename, study_id,
        region=None, bucket_index=1, rows=10000, output='.',
        filesystem=None):

    assert os.path.exists(vcf_filename), vcf_filename

    vcf_config = Configure.from_dict({
            'vcf': {
                'vcf': vcf_filename,
                'annotation': None,
            },
        })

    impala_config = Configure.from_prefix_impala(
        output, bucket_index=bucket_index, db=None, study_id=study_id).impala
    print("converting into ", impala_config, file=sys.stderr)

    fvars = RawVcfVariants(
        pedigree_df,
        config=vcf_config, annotator=VcfAlleleFrequencyAnnotator(),
        region=region, genomes_db=genomes_db
    )

    fvars.annot_df = annotation_pipeline.annotate_df(fvars.annot_df)

    return variants_iterator_to_parquet(
        fvars,
        impala_config,
        bucket_index=bucket_index,
        rows=rows,
        annotation_pipeline=annotation_pipeline,
        filesystem=filesystem
    )


def parse_cli_arguments(gpf_instance, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert VCF file to parquet',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='vcf import or make generation for vcf import')

    parse_vcf_arguments(gpf_instance, subparsers)
    parser_make_arguments(gpf_instance, subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


def parser_common_arguments(gpf_instance, parser):
    options = annotation_config_cli_options(gpf_instance)

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


def parse_vcf_arguments(gpf_instance, subparsers):
    parser = subparsers.add_parser('vcf')
    parser_common_arguments(gpf_instance, parser)

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


def parser_make_arguments(gpf_instance, subparsers):
    parser = subparsers.add_parser('make')
    parser_common_arguments(gpf_instance, parser)

    parser.add_argument(
        '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len> '
        '[default: %(default)s]'
    )


def generate_makefile(dae_config, genome, argv):
    assert os.path.exists(argv.vcf)
    assert os.path.exists(argv.pedigree)

    vcf_filename = argv.vcf
    ped_filename = argv.pedigree

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
    gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config
    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()

    argv = parse_cli_arguments(gpf_instance, sys.argv[1:])

    if argv.type == 'make':
        generate_makefile(dae_config, genome, argv)
    elif argv.type == 'vcf':
        annotation_pipeline = construct_import_annotation_pipeline(
            dae_config, genomes_db, argv)

        import_vcf(
            dae_config, genomes_db, annotation_pipeline,
            argv.pedigree, argv.vcf,
            region=argv.region, bucket_index=argv.bucket_index,
            output=argv.output)
