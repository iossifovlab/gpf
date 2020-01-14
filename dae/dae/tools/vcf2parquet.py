#!/usr/bin/env python

import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.pedigrees.loader import FamiliesLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescription

from cyvcf2 import VCF

from dae.backends.import_commons import construct_import_annotation_pipeline, \
        generate_makefile


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def cli_common_arguments(gpf_instance, parser):
    parser.add_argument(
        'families', type=str,
        metavar='<families filename>',
        help='families file in pedigree format'
    )

    FamiliesLoader.cli_arguments(parser)

    parser.add_argument(
        'vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )
    VcfLoader.cli_arguments(parser)

    parser.add_argument(
        '-o', '--out', type=str, default='.',
        dest='output', metavar='<output filepath prefix>',
        help='output filepath prefix. '
        'If none specified, current directory is used [default: %(default)s]'
    )

    parser.add_argument(
        '--pd', type=str, default=None,
        dest='partition_description',
        help='Path to a config file containing the partition description'
    )
    parser.add_argument(
        '--rows', type=int, default=100000,
        dest='rows',
        help='Amount of allele rows to write at once'
    )

    parser.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None, nargs='+',
        help='region to convert [default: %(default)s] '
        'ex. chr1:1-10000'
    )

    parser.add_argument(
        '--annotation-config', type=str, default=None,
        help='Path to an annotation config file to use when annotating'
    )


def cli_arguments(gpf_instance):
    parser = argparse.ArgumentParser(
        description='Convert VCF file to parquet',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='vcf import or make generation for vcf import')

    # VCF subcommand
    vcf_parser = subparsers.add_parser('vcf')
    cli_common_arguments(gpf_instance, vcf_parser)
    vcf_parser.add_argument(
        '-b', '--bucket-index', type=int, default=1,
        dest='bucket_index', metavar='bucket index',
        help='bucket index [default: %(default)s]'
    )

    # make subcommand
    make_parser = subparsers.add_parser('make')
    cli_common_arguments(gpf_instance, make_parser)

    return parser


def main(
        argv=sys.argv[1:],
        gpf_instance=None, dae_config=None, genomes_db=None, genome=None,
        annotation_defaults={}):

    if gpf_instance is None:
        gpf_instance = GPFInstance()
    if dae_config is None:
        dae_config = gpf_instance.dae_config
    if genomes_db is None:
        genomes_db = gpf_instance.genomes_db
    if genome is None:
        genome = genomes_db.get_genome()

    parser = cli_arguments(gpf_instance)
    argv = parser.parse_args(argv)

    families_loader = FamiliesLoader(argv.families)
    families = families_loader.load()

    vcf_files = [fn.strip() for fn in argv.vcf.split(',')]

    if argv.type == 'make':
        generate_makefile(
            genome, get_contigs(vcf_files[0]),
            f'vcf2parquet.py vcf {argv.families} {argv.vcf} ',
            argv)

    elif argv.type == 'vcf':
        annotation_pipeline = construct_import_annotation_pipeline(
            dae_config, genomes_db,
            annotation_configfile=argv.annotation_config,
            defaults=annotation_defaults)

        params = VcfLoader.parse_cli_arguments(argv)
        variants_loader = VcfLoader(
            families, vcf_files, regions=argv.region,
            params=params)

        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline
        )

        if argv.partition_description is None:

            filename_parquet = os.path.join(
                argv.output,
                'variant',
                'variants.parquet')

            ParquetManager.variants_to_parquet(
                variants_loader, filename_parquet,
                bucket_index=argv.bucket_index)
        else:
            description = ParquetPartitionDescription.from_config(
                    argv.partition_description)

            ParquetManager.variants_to_parquet_partition(
                    variants_loader, description,
                    argv.output,
                    bucket_index=argv.bucket_index,
                    rows=argv.rows
            )


if __name__ == "__main__":
    main(sys.argv[1:])
