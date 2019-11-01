#!/usr/bin/env python

import os
import sys
import argparse
import time
import glob
import shutil
import copy

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.tools.vcf2parquet import import_vcf
from dae.tools.dae2parquet import import_dae_denovo
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.pedigrees.pedigree_reader import PedigreeReader, PedigreeRoleGuesser


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


def parse_cli_arguments(argv=sys.argv[1:]):
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

    add_cli_arguments_pedigree(parser)

    parser_args = parser.parse_args(argv)
    return parser_args


STUDY_CONFIG_TEMPLATE = """
[study]

id = {id}
prefix = {output}
file_format = impala

"""


def impala_load_study(dae_config, study_id, parquet_directory):
    impala_helpers = ImpalaHelpers(
        dae_config.impala.host, dae_config.impala.port)
    hdfs_helpers = HdfsHelpers(
        dae_config.hdfs.host, dae_config.hdfs.port
    )
    variant_glob = os.path.join(
        parquet_directory,
        "{}_variant*.parquet".format(study_id))
    pedigree_glob = os.path.join(
        parquet_directory,
        "{}_pedigree.parquet".format(study_id))

    hdfs_dirname = os.path.join(dae_config.hdfs.base_dir, study_id)
    if not hdfs_helpers.hdfs.exists(hdfs_dirname):
        hdfs_helpers.hdfs.mkdir(hdfs_dirname)

    variant_files = []
    for variant_filename in glob.glob(variant_glob):
        print(variant_filename)
        basename = os.path.basename(variant_filename)
        hdfs_filename = os.path.join(hdfs_dirname, basename)
        variant_files.append(hdfs_filename)
        hdfs_helpers.put(variant_filename, hdfs_filename)

    pedigree_files = []
    for pedigree_filename in glob.glob(pedigree_glob):
        print(pedigree_filename)
        basename = os.path.basename(pedigree_filename)
        hdfs_filename = os.path.join(hdfs_dirname, basename)
        pedigree_files.append(hdfs_filename)
        hdfs_helpers.put(pedigree_filename, hdfs_filename)

    dbname = dae_config.impala.db
    pedigree_table = "{}_pedigree".format(study_id)
    variant_table = "{}_variant".format(study_id)
    variant_glob = os.path.join(
        hdfs_dirname, "{}_variant*.parquet".format(study_id)
    )
    with impala_helpers.connection.cursor() as cursor:
        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS {db}
        """.format(db=dbname))

        impala_helpers.import_pedigree_file(
            cursor, dbname, pedigree_table, pedigree_files[0])
        impala_helpers.import_variant_files(
            cursor, dbname, variant_table, variant_files)


def generate_study_config(dae_config, study_id, output):
    assert study_id is not None

    dirname = os.path.join(dae_config.studies_db.dir, study_id)
    filename = os.path.join(dirname, "{}.conf".format(study_id))

    if os.path.exists(filename):
        print("configuration file already exists:", filename)
        print("skipping generation of default config for:", study_id)
        return

    with open(filename, 'w') as outfile:
        outfile.write(STUDY_CONFIG_TEMPLATE.format(
            id=study_id,
            output=argv.output
        ))


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

    argv = parse_cli_arguments(sys.argv[1:])
    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.pedigree))

    if argv.output is None:
        output = os.path.join(
            dae_config.studies_db.dir, study_id, 'parquet'
        )
    else:
        output = argv.output
    print("storing results into: ", output, file=sys.stderr)
    os.makedirs(output, exist_ok=True)

    assert argv.vcf is not None or argv.denovo is not None

    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()
    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, genomes_db, argv)

    # handle pedigree
    if argv.ped_no_header:
        argv = cast_pedigree_column_indices_to_int(argv)
    ped_df = PedigreeReader.load_pedigree_file(
        argv.pedigree,
        sep='\t',
        col_family=argv.ped_family,
        col_person=argv.ped_person,
        col_mom=argv.ped_mom,
        col_dad=argv.ped_dad,
        col_sex=argv.ped_sex,
        col_status=argv.ped_status,
        col_role=argv.ped_role,
    )
    if argv.ped_no_role:
        ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)

    denovo_parquet = None
    vcf_parquet = None

    if argv.vcf is not None:
        vcf_parquet = import_vcf(
            dae_config, genomes_db, annotation_pipeline,
            ped_df, argv.vcf, study_id,
            output=output
        )
    if argv.denovo is not None:
        denovo_parquet = import_dae_denovo(
            dae_config, genome, annotation_pipeline,
            ped_df, argv.denovo,
            output=output, family_format='pedigree',
            study_id=study_id,
        )
    if argv.denovo is None and argv.vcf is not None:
        assert denovo_parquet is None
        assert vcf_parquet is not None
        pedigree_filename = os.path.join(
            output, "{}_pedigree.parquet".format(study_id))
        shutil.copyfile(
            vcf_parquet.files.pedigree,
            pedigree_filename
        )
        assert os.path.exists(pedigree_filename), pedigree_filename

    generate_study_config(dae_config, study_id, output)
    impala_load_study(dae_config, study_id, output)

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
