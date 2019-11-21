#!/usr/bin/env python

import os
import sys
import time
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.backends.import_commons import variants2parquet
from dae.backends.dae.loader import DenovoLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator

from dae.pedigrees.family import PedigreeReader, PedigreeRoleGuesser
from dae.pedigrees.family import FamiliesData


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
    default_genotype_storage_id = \
        dae_config.get('genotype_storage', {}).get('default', None)

    parser = argparse.ArgumentParser(
        description='simple import of new study data',
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        '--id', type=str,
        metavar='<study ID>',
        dest="id",
        help='Unique study ID to use. '
        'If not specified the basename of the family pedigree file is used '
        'for study ID'
    )

    parser.add_argument(
        '--vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )

    parser.add_argument(
        '--denovo', type=str,
        metavar='<de Novo variants filename>',
        help='DAE denovo variants file'
    )

    parser.add_argument(
        '-o', '--out', type=str, default=None,
        dest='output', metavar='<output directory>',
        help='output directory for storing intermediate parquet files. '
        'If none specified, "parquet/" directory inside GPF instance '
        'study directory is used [default: %(default)s]'
    )

    parser.add_argument(
        '--skip-reports',
        help='skip running report generation [default: %(default)s]',
        default=False,
        action='store_true',
    )

    parser.add_argument(
        '--genotype-storage', type=str,
        metavar='<genotype storage id>',
        dest='genotype_storage',
        help='Id of defined in DAE.conf genotype storage '
             '[default: %(default)s]',
        default=default_genotype_storage_id,
        action='store'
    )

    PedigreeReader.flexible_pedigree_cli_arguments(parser)
    DenovoLoader.flexible_denovo_cli_arguments(parser)

    parser_args = parser.parse_args(argv)
    return parser_args


def save_study_config(dae_config, study_id, study_config):
    dirname = os.path.join(dae_config.studies_db.dir, study_id)
    filename = os.path.join(dirname, '{}.conf'.format(study_id))

    if os.path.exists(filename):
        print('configuration file already exists:', filename)
        print('skipping generation of default study config for:', study_id)
        return

    os.makedirs(dirname, exist_ok=True)
    with open(filename, 'w') as outfile:
        outfile.write(study_config)


def generate_common_report(gpf_instance, study_id):
    from dae.tools.generate_common_report import main
    argv = ['--studies', study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def generate_denovo_gene_sets(gpf_instance, study_id):
    from dae.tools.generate_denovo_gene_sets import main
    argv = ['--studies', study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def main(argv, gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    dae_config = gpf_instance.dae_config

    argv = parse_cli_arguments(dae_config, argv)

    genotype_storage_factory = gpf_instance.genotype_storage_factory
    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()

    genotype_storage = genotype_storage_factory.get_genotype_storage(
        argv.genotype_storage
    )
    print("genotype storage:", argv.genotype_storage, genotype_storage)
    assert genotype_storage is not None, argv.genotype_storage

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, genomes_db, argv)
    parquet_manager = ParquetManager(dae_config.studies_db.dir)

    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.pedigree))

    if argv.output is None:
        output = parquet_manager.get_data_dir(study_id)
    else:
        output = argv.output

    print("storing results into: ", output, file=sys.stderr)
    os.makedirs(output, exist_ok=True)

    assert output is not None
    assert argv.vcf is not None or argv.denovo is not None

    has_header = True
    if argv.ped_no_header:
        argv = PedigreeReader.cast_pedigree_column_indices_to_int(argv)

    ped_df = PedigreeReader.flexible_pedigree_read(
        argv.pedigree,
        col_family=argv.ped_family,
        col_person=argv.ped_person,
        col_mom=argv.ped_mom,
        col_dad=argv.ped_dad,
        col_sex=argv.ped_sex,
        col_status=argv.ped_status,
        col_role=argv.ped_role,
        has_header=has_header)

    if argv.ped_no_role:
        ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)
    families = FamiliesData.from_pedigree_df(ped_df)

    skip_pedigree = False
    if argv.vcf and argv.denovo:
        skip_pedigree = True

    parquet_filenames = None
    if argv.vcf is not None:
        variants_loader = VcfLoader(
            families,
            argv.vcf
        )
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline
        )
        parquet_filenames = variants2parquet(
            study_id, variants_loader,
            output=output, bucket_index=100,
            skip_pedigree=skip_pedigree,
        )

    if argv.denovo is not None:
        variants_loader = DenovoLoader(
            families,
            argv.denovo,
            genome=genome,
            denovo_format={
                'location': argv.denovo_location,
                'variant': argv.denovo_variant,
                'chrom': argv.denovo_chrom,
                'pos': argv.denovo_pos,
                'ref': argv.denovo_ref,
                'alt': argv.denovo_alt,
                'person_id': argv.denovo_person_id,
                'family_id': argv.denovo_family_id,
                'best_state': argv.denovo_best_state,
                'families': families,
            }
        )
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline
        )
        parquet_filenames = variants2parquet(
            study_id, variants_loader,
            output=output, bucket_index=0
        )

    if parquet_filenames:
        study_config = genotype_storage.impala_load_study(
            study_id,
            os.path.split(parquet_filenames.pedigree)[0],
            os.path.split(parquet_filenames.variant)[0]
        )
        print(study_config)

        save_study_config(dae_config, study_id, study_config)

    if not argv.skip_reports:
        # needs to reload the configuration, hence gpf_instance=None
        gpf_instance.reload_variants_db()

        print("generating common reports...", file=sys.stderr)
        start = time.time()
        generate_common_report(gpf_instance, study_id)
        print("DONE: generating common reports in {:.2f} sec".format(
            time.time() - start
            ), file=sys.stderr)

        print("generating de Novo gene sets...", file=sys.stderr)
        start = time.time()
        generate_denovo_gene_sets(gpf_instance, study_id)
        print("DONE: generating de Novo gene sets in {:.2f} sec".format(
            time.time() - start
            ), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])