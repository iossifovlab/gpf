#!/usr/bin/env python

import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.annotation.tools.annotator_config import annotation_config_cli_options

from dae.pedigrees.family import FamiliesData
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.parquet_io import ParquetManager

from cyvcf2 import VCF

from dae.backends.import_commons import build_contig_regions, \
    contigs_makefile_generate, variants2parquet
from dae.backends.import_commons import construct_import_annotation_pipeline


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
    parser.add_argument(
        '--include-reference', default=False,
        dest='include_reference',
        help='include reference only variants [default: %(defaults)s]',
        action='store_true'
    )
    parser.add_argument(
        '--include-unknown', default=False,
        dest='include_unknown',
        help='include variants with unknown genotype [default: %(defaults)s]',
        action='store_true'
    )
    parser.add_argument(
        '--study-id', default=None,
        dest='study_id',
        help='specifies study id to use when storing parquet files '
        '[default: %(defaults)s]'
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


def vcf2parquet(
        study_id, ped_df, vcf_filename,
        genomes_db, annotation_pipeline,
        output='.', bucket_index=1, region=None,
        filesystem=None, skip_pedigree=False,
        include_reference=False, include_unknown=False):

    assert os.path.exists(vcf_filename), vcf_filename

    parquet_filenames = ParquetManager.build_parquet_filenames(
        output, bucket_index=bucket_index, study_id=study_id
    )
    print("converting into ", parquet_filenames.variant, file=sys.stderr)

    families = FamiliesData.from_pedigree_df(ped_df)
    variants_loader = VcfLoader(families, vcf_filename, region=region)
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline)

    if not skip_pedigree:
        ParquetManager.pedigree_to_parquet(
            variants_loader, parquet_filenames.pedigree, filesystem=filesystem
        )

    ParquetManager.variants_to_parquet(
        variants_loader, parquet_filenames.variant,
        bucket_index=bucket_index,
        include_reference=include_reference,
        include_unknown=include_unknown,
        filesystem=filesystem
    )

    return parquet_filenames


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

    if argv.type == 'make':
        generate_makefile(dae_config, genome, argv)
    elif argv.type == 'vcf':
        families = FamiliesData.load_pedigree(argv.pedigree)
        variants_loader = VcfLoader(families, argv.vcf, region=argv.region)
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline
        )

        parquet_filenames = variants2parquet(
            study_id, variants_loader,
            output=argv.output, bucket_index=argv.bucket_index,
            skip_pedigree=argv.skip_pedigree,
            include_reference=argv.include_reference,
            include_unknown=argv.include_unknown
        )
        return parquet_filenames


if __name__ == "__main__":
    main(sys.argv[1:])
