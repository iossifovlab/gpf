#!/usr/bin/env python

import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.dae.loader import DenovoLoader
from dae.backends.impala.import_commons import \
    construct_import_annotation_pipeline
from dae.backends.impala.parquet_io import ParquetManager

from dae.pedigrees.loader import FamiliesLoader


def cli_arguments_parser(gpf_instance):
    parser = argparse.ArgumentParser(
        description='Convert de Novo family variants file to parquet',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    FamiliesLoader.cli_arguments(parser)

    parser.add_argument(
        '-o', '--out', type=str, default='./variants.parquet',
        dest='output', metavar='output filename',
        help='output filepath.  [default: %(default)s]'
    )
    parser.add_argument(
        '-b', '--bucket-index', type=int,
        default=0,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )

    parser.add_argument(
        '--rows', type=int,
        default=100000,
        dest='rows', metavar='rows',
        help='row group size'
    )

    parser.add_argument(
        '--annotation-config', type=str, default=None,
        help='Path to an annotation config file to use when annotating'
    )

    DenovoLoader.cli_arguments(parser)
    return parser


def main(argv, gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    parser = cli_arguments_parser(gpf_instance)
    argv = parser.parse_args(argv)

    families_filename, families_params = \
        FamiliesLoader.parse_cli_arguments(argv)
    families_loader = FamiliesLoader(
        families_filename,
        params=families_params)
    families = families_loader.load()

    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance,
        annotation_configfile=argv.annotation_config
    )

    denovo_filename, denovo_params = DenovoLoader.parse_cli_arguments(argv)
    variants_loader = DenovoLoader(
        families, denovo_filename, gpf_instance.genomes_db.get_genome(),
        params=denovo_params)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline)

    output = argv.output
    os.makedirs(os.path.dirname(output), exist_ok=True)

    ParquetManager.variants_to_parquet_filename(
        variants_loader, output,
        bucket_index=argv.bucket_index
    )


if __name__ == "__main__":
    main(sys.argv[1:])
