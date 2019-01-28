#!/usr/bin/env python

'''
Created on Jun 4, 2018

@author: lubo
'''
from __future__ import print_function

import os
import sys
import time
import argparse

from backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator
from backends.vcf.annotate_composite import AnnotatorComposite
from backends.vcf.annotate_variant_effects import VcfVariantEffectsAnnotator
from backends.vcf.builder import get_genome, get_gene_models
from backends.configure import Configure
from backends.thrift.parquet_io import VariantsParquetWriter, \
    save_ped_df_to_parquet
from backends.vcf.raw_vcf import RawFamilyVariants
from cyvcf2 import VCF

from backends.import_commons import build_contig_regions, \
    contigs_makefile_generate

# import multiprocessing
# import functools


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def create_vcf_variants(
        config, region=None, 
        genome_file=None, gene_models_file=None):

    genome = get_genome(genome_file=genome_file)
    gene_models = get_gene_models(gene_models_file=gene_models_file)

    effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        freq_annotator
    ])

    fvars = RawFamilyVariants(
        config=config, annotator=annotator,
        region=region)
    return fvars


def import_pedigree(config):
    pedigree_filename = os.path.join(
        config.output,
        "pedigree.parquet",
    )
    region = "1:1-100000"
    fvars = create_vcf_variants(config, region)
    save_ped_df_to_parquet(fvars.ped_df, pedigree_filename)


def import_vcf(argv):
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

    if fvars.is_empty():
        print("empty contig {} done".format(region), file=sys.stderr)
        return

    parquet_config = Configure.from_prefix_parquet(argv.output).parquet
    print("converting into ", parquet_config)

    save_ped_df_to_parquet(fvars.ped_df, parquet_config.pedigree)

    print("going to build: ", argv.region)
    start = time.time()

    variants_writer = VariantsParquetWriter(fvars.full_variants_iterator())
    variants_writer.save_variants_to_parquet(
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=argv.bucket_index)
    end = time.time()

    print("DONE region: {} for {} sec".format(
        argv.region, round(end-start)))


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert VCF file to parquet')

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='vcf import or make generation for vcf import')

    parse_vcf_arguments(subparsers)
    parser_make_arguments(subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


def parser_common_arguments(parser):
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
        'If none specified, current directory is used'
    )


def parse_vcf_arguments(subparsers):
    parser = subparsers.add_parser('vcf')
    parser_common_arguments(parser)

    parser.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert'
    )

    parser.add_argument(
        '-b', '--bucket-index', type=int, default=1,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )


def parser_make_arguments(subparsers):
    parser = subparsers.add_parser('make')
    parser_common_arguments(parser)

    parser.add_argument(
        '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len>'
    )


def makefile_generate(argv):
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
        "{} {}".format(ped_filename, vcf_filename)
    )

# def reindex(argv):
#     for contig in SPARK_CONTIGS:
#         filename = "spark_summary_{}.parquet".format(contig)
#         # filename = "spark_variants_{}.parquet".format(contig)
#         parquet_file = pq.ParquetFile(filename)
#         print(filename)
#         print(parquet_file.metadata)
#         print("row_groups:", parquet_file.num_row_groups)
#         print(parquet_file.schema)


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])

    if argv.type == 'vcf':
        import_vcf(argv)
    elif argv.type == 'make':
        makefile_generate(argv)
