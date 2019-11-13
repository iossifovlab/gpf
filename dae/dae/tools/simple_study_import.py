#!/usr/bin/env python

import os
import sys
import time
import glob
import shutil
import copy
from functools import partial
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.utils.helpers import add_flexible_denovo_import_args, \
    read_variants_from_dsv

from dae.tools.vcf2parquet import import_vcf
from dae.tools.dae2parquet import import_dae_denovo
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.pedigrees.pedigree_reader import PedigreeReader, PedigreeRoleGuesser
from dae.pedigrees.family import FamiliesData

from dae.tools.vcf2parquet import vcf2parquet
from dae.tools.dae2parquet import denovo2parquet


def add_cli_arguments_pedigree(parser):
    parser.add_argument(
        '--ped-family',
        default='familyId',
        help='specify the name of the column in the pedigree file that holds '
        'the ID of the family the person belongs to [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-person',
        default='personId',
        help='specify the name of the column in the pedigree file that holds '
        'the person\'s ID [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-mom',
        default='momId',
        help='specify the name of the column in the pedigree file that holds '
        'the ID of the person\'s mother [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-dad',
        default='dadId',
        help='specify the name of the column in the pedigree file that holds '
        'the ID of the person\'s father [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-sex',
        default='sex',
        help='specify the name of the column in the pedigree file that holds '
        'the sex of the person [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-status',
        default='status',
        help='specify the name of the column in the pedigree file that holds '
        'the status of the person [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-role',
        default='role',
        help='specify the name of the column in the pedigree file that holds '
        'the role of the person [default: %(default)s]'
    )

    parser.add_argument(
        '--ped-no-role',
        action='store_true',
        help='indicates that the provided pedigree file has no role column. '
        'If this argument is provided, the import tool will guess the roles '
        'of individuals and write them in a "role" column.'
    )

    parser.add_argument(
        '--ped-no-header',
        action='store_true',
        help='indicates that the provided pedigree file has no header. The '
        'pedigree column arguments will accept indices if this argument is '
        'given. [default: %(default)s]'
    )


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

    add_cli_arguments_pedigree(parser)
    add_flexible_denovo_import_args(parser)

    parser_args = parser.parse_args(argv)
    return parser_args


STUDY_CONFIG_TEMPLATE = """
[study]

id = {id}
prefix = {output}
file_format = impala

"""


def generate_common_report(gpf_instance, study_id):
    from dae.tools.generate_common_report import main
    argv = ['--studies', study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def generate_denovo_gene_sets(gpf_instance, study_id):
    from dae.tools.generate_denovo_gene_sets import main
    argv = ['--studies', study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def cast_pedigree_column_indices_to_int(argv):
    ped_col_args = [
        'ped_family',
        'ped_person',
        'ped_mom',
        'ped_dad',
        'ped_sex',
        'ped_status',
        'ped_role',
    ]
    res_argv = copy.deepcopy(argv)

    for col in ped_col_args:
        col_idx = getattr(argv, col)
        assert col_idx.isnumeric(), \
            '{} must hold an integer value!'.format(col)
        setattr(res_argv, col, int(col_idx))

    return res_argv


if __name__ == "__main__":
    gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config

    argv = parse_cli_arguments(dae_config, sys.argv[1:])

    genotype_storage_factory = gpf_instance.genotype_storage_factory
    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()


    genotype_storage = genotype_storage_factory.get_genotype_storage(
        argv.genotype_storage
    )
    print("genotype storage:", argv.genotype_storage, genotype_storage)

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

    # handle pedigree
    load_pedigree_partial = partial(
        PedigreeReader.load_pedigree_file,
        col_family=argv.ped_family,
        col_person=argv.ped_person,
        col_mom=argv.ped_mom,
        col_dad=argv.ped_dad,
        col_sex=argv.ped_sex,
        col_status=argv.ped_status,
        col_role=argv.ped_role,
    )

    if argv.ped_no_header:
        argv = cast_pedigree_column_indices_to_int(argv)
        ped_df = load_pedigree_partial(argv.pedigree, has_header=False)
    else:
        ped_df = load_pedigree_partial(argv.pedigree)

    if argv.ped_no_role:
        ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)
    families = FamiliesData.from_pedigree_df(ped_df)

    denovo_parquet = None
    vcf_parquet = None

    skip_pedigree = False
    if argv.vcf and argv.denovo:
        skip_pedigree = True

    parquet_config = None
    if argv.vcf is not None:
        parquet_config = vcf2parquet(
            ped_df, argv.vcf,
            genomes_db, annotation_pipeline, parquet_manager,
            output=output, bucket_index=1
        )
    if argv.denovo is not None:
        print("denovo filename:", argv.denovo)
        denovo_df = read_variants_from_dsv(
            argv.denovo,
            genome,
            location=argv.denovo_location,
            variant=argv.denovo_variant,
            chrom=argv.denovo_chrom,
            pos=argv.denovo_pos,
            ref=argv.denovo_ref,
            alt=argv.denovo_alt,
            personId=argv.denovo_personId,
            familyId=argv.denovo_familyId,
            bestSt=argv.denovo_bestSt,
            families=families,
        )
        print(denovo_df.head())

        parquet_config = denovo2parquet(
            study_id, ped_df, denovo_df,
            parquet_manager, annotation_pipeline, genome,
            output=output, bucket_index=0, skip_pedigree=skip_pedigree
        )

    if parquet_config:
        genotype_storage.impala_load_study(
            study_id,
            os.path.split(parquet_config.files.pedigree)[0],
            os.path.split(parquet_config.files.variant)[0]
        )

    parquet_manager.generate_study_config(
        study_id, genotype_storage.storage_config.id
    )

    if not argv.skip_reports:
        # needs to reload the configuration, hence gpf_instance=None
        gpf_instance_reload = GPFInstance()

        print("generating common reports...", file=sys.stderr)
        start = time.time()
        generate_common_report(gpf_instance_reload, study_id)
        print("DONE: generating common reports in {:.2f} sec".format(
            time.time() - start
            ), file=sys.stderr)

        print("generating de Novo gene sets...", file=sys.stderr)
        start = time.time()
        generate_denovo_gene_sets(gpf_instance_reload, study_id)
        print("DONE: generating de Novo gene sets in {:.2f} sec".format(
            time.time() - start
            ), file=sys.stderr)
