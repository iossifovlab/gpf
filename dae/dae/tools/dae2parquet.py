#!/usr/bin/env python

import os
import sys
from box import Box

import pysam
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader

from dae.backends.import_commons import build_contig_regions, \
    contigs_makefile_generate

from dae.backends.import_commons import construct_import_annotation_pipeline, \
    generate_makefile

from dae.pedigrees.family import FamiliesLoader
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescription


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:
        return tbx.contigs


def dae_build_transmitted(annotation_pipeline, genome, argv):

    config = Box({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    assert argv.output is not None
    ped_params = FamiliesLoader.parse_cli_arguments(argv)
    families_loader = FamiliesLoader(
        config.dae.family_filename,
        params=ped_params
    )
    families = families_loader.load()

    fvars = DaeTransmittedLoader(
        families,
        config.dae.summary_filename,
        config.dae.toomany_filename,
        genome=genome,
        region=argv.region,
    )

    return fvars


def dae_build_makefile(dae_config, genome, argv):
    data_contigs = get_contigs(argv.summary)
    build_contigs = build_contig_regions(genome, argv.len)

    family_format = ""
    if argv.family_format == 'simple':
        family_format = "-f simple"
    elif argv.family_format == 'pedigree':
        family_format = "-f pedigree"
    else:
        raise ValueError("unexpected family format: {}".format(
            argv.family_format
        ))
    no_reference = ""
    if argv.no_reference:
        no_reference = "--no-reference"

    env = ""
    if argv.env:
        env = "{} ".format(argv.env)

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.output,
        'dae2parquet.py dae {family_format} {no_reference}'.format(
            family_format=family_format,
            no_reference=no_reference,
            env=env),
        argv.annotation_config,
        "{family_filename} {summary_filename} {toomany_filename}".format(
            family_filename=argv.families,
            summary_filename=argv.summary,
            toomany_filename=argv.toomany),
        rows=argv.rows,
        log_directory=argv.log,
        env=env
    )


def init_parser_dae_common(gpf_instance, parser):
    parser.add_argument(
        'families', type=str,
        metavar='<families filename>',
        help='families file in pedigree format'
    )

    FamiliesLoader.cli_arguments(parser)

    # options = annotation_config_cli_options(gpf_instance)
    # for name, args in options:
    #     parser.add_argument(name, **args)

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
    # parser.add_argument(
    #     '-f', '--family-format', type=str,
    #     default='pedigree',
    #     dest='family_format',
    #     help='families file format - `pedigree` or `simple`; '
    #     '[default: %(default)s]'
    # )

    parser.add_argument(
        '--no-reference', action="store_true", default=None,
        help="Skip reference alleles and all unknown alleles"
    )

    parser.add_argument(
        '--rows', type=int,
        default=100000,
        dest='rows', metavar='rows',
        help='row group size'
    )

    parser.add_argument(
        '--skip-pedigree',
        help='skip import of pedigree file [default: %(default)s]',
        default=False,
        action='store_true',
    )

    parser.add_argument(
        '--pd', type=str, default=None,
        dest='partition_description',
        help='Path to a config file containing the partition description'
    )


def init_parser_denovo(gpf_instance, subparsers):
    parser_denovo = subparsers.add_parser('denovo')
    init_parser_dae_common(gpf_instance, parser_denovo)

    parser_denovo.add_argument(
        'variants', type=str,
        metavar='<variants filename>',
        help='DAE denovo variants file'
    )

    DenovoLoader.cli_arguments(parser_denovo)


def init_transmitted_common(gpf_instance, parser):

    init_parser_dae_common(gpf_instance, parser)

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


def init_parser_dae(gpf_instance, subparsers):
    parser_dae = subparsers.add_parser('dae')

    init_transmitted_common(gpf_instance, parser_dae)

    parser_dae.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert'
    )


def init_parser_make(gpf_instance, subparsers):
    parser = subparsers.add_parser('make')

    init_transmitted_common(gpf_instance, parser)

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

    parser.add_argument(
        '--env', type=str,
        default=None,
        dest='env', metavar='<ENV options>',
        help='additional environment options'
    )

    parser.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        default=None,
        help='region to convert'
    )


def parse_cli_arguments(gpf_instance, argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert DAE file to parquet')

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='denovo or transmitted study')

    init_parser_denovo(gpf_instance, subparsers)
    init_parser_dae(gpf_instance, subparsers)
    init_parser_make(gpf_instance, subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


def denovo2parquet(
        family_filename, denovo_filename,
        annotation_pipeline, genome, argv,
        output='.', bucket_index=0, rows=10000, filesystem=None,
        skip_pedigree=False,
        ped_params={}, denovo_params={}):

    families_loader = FamiliesLoader(
        family_filename,
        params=ped_params)
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families_loader.families, denovo_filename, genome,
        params=denovo_params)
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline)

    if not skip_pedigree:
        pedigree_path = os.path.join(
            argv.output,
            'pedigree',
            'pedigree.ped')
        ParquetManager.pedigree_to_parquet(
            families, pedigree_path)

    if argv.partition_description is None:
        filename = os.path.join(argv.output, 'variant', 'variants.parquet')
        ParquetManager.variants_to_parquet(
            variants_loader, filename,
            rows=rows, bucket_index=bucket_index,
            filesystem=filesystem
        )
    else:
        description = ParquetPartitionDescription.from_config(
                    argv.partition_description)

        ParquetManager.variants_to_parquet_partition(
            variants_loader, description,
            argv.output,
            bucket_index=argv.bucket_index
        )


def dae2parquet(
        dae_config, parquet_manager, annotation_pipeline, genome, argv):
    filename = os.path.basename(argv.families)
    study_id = os.path.splitext(filename)[0]
    print(filename, os.path.splitext(filename), study_id)
    fvars = dae_build_transmitted(annotation_pipeline, genome, argv)
    fvars = AnnotationPipelineDecorator(fvars, annotation_pipeline)

    if not argv.skip_pedigree:
        pedigree_path = os.path.join(
            argv.output,
            'pedigree',
            'pedigree.ped')
        ParquetManager.pedigree_to_parquet(
            fvars, pedigree_path)

    if argv.partition_description is None:
        filename = os.path.join(argv.output, 'variant', 'variants.parquet')

        parquet_manager.variants_to_parquet(
            fvars, filename,
            bucket_index=argv.bucket_index,
            rows=argv.rows
        )
    else:
        description = ParquetPartitionDescription.from_config(
            argv.partition_description)

        parquet_manager.variants_to_parquet_partition(
            fvars, description,
            argv.output,
            bucket_index=argv.bucket_index,
            rows=argv.rows
        )


def main(argv):
    gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config
    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()
    parquet_manager = ParquetManager(dae_config.studies_db.dir)

    argv = parse_cli_arguments(gpf_instance, argv)
    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, genomes_db, argv)

    if argv.type == 'denovo':
        denovo_params = DenovoLoader.parse_cli_arguments(argv)
        ped_params = FamiliesLoader.parse_cli_arguments(argv)

        denovo2parquet(
            argv.families, argv.variants,
            annotation_pipeline, genome,
            argv,
            output=argv.output, bucket_index=0, rows=argv.rows,
            skip_pedigree=argv.skip_pedigree,
            ped_params=ped_params,
            denovo_params=denovo_params
        )
    elif argv.type == 'dae':
        dae2parquet(
            dae_config, parquet_manager, annotation_pipeline, genome, argv
        )
    elif argv.type == 'make':
        fvars = dae_build_transmitted(annotation_pipeline, genome, argv)
        fvars = AnnotationPipelineDecorator(fvars, annotation_pipeline)
        generate_makefile(
            fvars,
            f'dae2parquet.py dae {argv.families} '
            f'{argv.summary} {argv.toomany} ',
            argv
        )


if __name__ == "__main__":
    main(sys.argv[1:])
