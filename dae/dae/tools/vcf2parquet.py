#!/usr/bin/env python

import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.annotation.tools.annotator_config import annotation_config_cli_options

from dae.pedigrees.family import FamiliesLoader  # , FamiliesData
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

    parser_vcf_arguments(gpf_instance, subparsers)
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
        '--include-reference', default=False,
        dest='include_reference',
        help='include reference only variants [default: %(default)s]',
        action='store_true'
    )
    parser.add_argument(
        '--include-unknown', default=False,
        dest='include_unknown',
        help='include variants with unknown genotype [default: %(default)s]',
        action='store_true'
    )

    parser.add_argument(
        '--study-id', default=None,
        dest='study_id',
        help='specifies study id to use when storing parquet files '
        '[default: %(default)s]'
    )

    parser.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None, nargs='+',
        help='region to convert [default: %(default)s] '
        'ex. chr1:1-10000'
    )


def parser_vcf_arguments(gpf_instance, subparsers):
    parser = subparsers.add_parser('vcf')
    parser_common_arguments(gpf_instance, parser)

    parser.add_argument(
        '-b', '--bucket-index', type=int, default=1,
        dest='bucket_index', metavar='bucket index',
        help='bucket index [default: %(default)s]'
    )

    parser.add_argument(
        '--skip-pedigree',
        help='skip import of pedigree file [default: %(default)s]',
        default=False,
        action='store_true',
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


def main(
        argv,
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

    argv = parse_cli_arguments(gpf_instance, argv)

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, genomes_db, argv, defaults=annotation_defaults)

    study_id = argv.study_id
    if study_id is None:
        study_id = os.path.splitext(os.path.basename(argv.pedigree))[0]
    families_loader = FamiliesLoader(argv.pedigree)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families, argv.vcf, regions=argv.region,
        params={
            'include_reference_genotypes': argv.include_reference,
            'include_unknown_family_genotypes': argv.include_unknown,
            'include_unknown_person_genotypes': argv.include_unknown
        })
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline
    )
    if argv.type == 'make':
        generate_makefile(variants_loader, 'vcf2parquet.py vcf ', argv)
    elif argv.type == 'vcf':
        if not argv.skip_pedigree:
            pedigree_path = os.path.join(
                argv.output,
                'pedigree',
                'pedigree.ped')
            ParquetManager.pedigree_to_parquet(
                families, pedigree_path)

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
