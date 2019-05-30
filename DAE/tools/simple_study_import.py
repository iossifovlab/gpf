#!/usr/bin/env python

from __future__ import print_function, absolute_import

import os
import sys
import argparse
import time
import glob
import shutil

from configurable_entities.configuration import DAEConfig
from backends.thrift.import_tools import construct_import_annotation_pipeline

from tools.vcf2parquet import import_vcf
from tools.dae2parquet import import_dae_denovo
from backends.impala.impala_backend import ImpalaBackend


def parse_cli_arguments(dae_config, argv=sys.argv[1:]):
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
        help='unique study ID to use'
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
        '-o', '--out', type=str, default='data/',
        dest='output', metavar='<output directory>',
        help='output directory. '
        'If none specified, "data/" directory is used [default: %(default)s]'
    )

    parser.add_argument(
        '--skip-reports',
        help='skip running report generation [default: %(default)s]',
        default=False,
        action='store_true',
    )
    parser_args = parser.parse_args(argv)
    return parser_args


STUDY_CONFIG_TEMPLATE = """
[study]

id = {id}
prefix = {output}

"""


def impala_load_study(dae_config, study_id, parquet_directory):
    backend = ImpalaBackend(
        dae_config.impala_host, dae_config.impala_port,
        dae_config.hdfs_host, dae_config.hdfs_port)

    variant_glob = os.path.join(
        parquet_directory,
        "{}_variant*.parquet".format(study_id))
    pedigree_glob = os.path.join(
        parquet_directory,
        "{}_pedigree.parquet".format(study_id))

    hdfs_dirname = os.path.join(dae_config.hdfs_base_dir, study_id)
    if not backend.hdfs.exists(hdfs_dirname):
        backend.hdfs.mkdir(hdfs_dirname)

    variant_files = []
    for variant_filename in glob.glob(variant_glob):
        print(variant_filename)
        basename = os.path.basename(variant_filename)
        hdfs_filename = os.path.join(hdfs_dirname, basename)
        variant_files.append(hdfs_filename)
        backend.hdfs.put(variant_filename, hdfs_filename)

    pedigree_files = []
    for pedigree_filename in glob.glob(pedigree_glob):
        print(pedigree_filename)
        basename = os.path.basename(pedigree_filename)
        hdfs_filename = os.path.join(hdfs_dirname, basename)
        pedigree_files.append(hdfs_filename)
        backend.hdfs.put(pedigree_filename, hdfs_filename)

    dbname = dae_config.impala_db
    pedigree_table = "{}_pedigree".format(study_id)
    variant_table = "{}_variant".format(study_id)
    variant_glob = os.path.join(
        hdfs_dirname, "{}_variant*.parquet".format(study_id)
    )
    with backend.impala.cursor() as cursor:
        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS {db}
        """.format(db=dbname))

        backend.import_pedigree_file(
            cursor, dbname, pedigree_table, pedigree_files[0])
        backend.import_variant_files(
            cursor, dbname, variant_table, variant_files)


def generate_study_config(dae_config, study_id, argv):
    assert study_id is not None
    assert argv.output is not None

    dirname = os.path.join(dae_config.studies_dir, study_id)
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


def generate_common_report(dae_config, study_id):
    from tools.generate_common_report import main
    argv = ['--studies', study_id]
    main(dae_config, argv)


if __name__ == "__main__":
    dae_config = DAEConfig()
    argv = parse_cli_arguments(dae_config, sys.argv[1:])
    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.pedigree))

    output = os.path.join(
        dae_config.studies_dir, study_id, argv.output
    )
    print("storing results into: ", output, file=sys.stderr)
    os.makedirs(output, exist_ok=True)

    assert argv.vcf is not None or argv.denovo is not None

    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config, argv)

    denovo_parquet = None
    vcf_parquet = None

    if argv.vcf is not None:
        vcf_parquet = import_vcf(
            dae_config, annotation_pipeline,
            argv.pedigree, argv.vcf,
            output=output, study_id=study_id)
    if argv.denovo is not None:
        denovo_parquet = import_dae_denovo(
            dae_config, annotation_pipeline,
            argv.pedigree, argv.denovo,
            output=output, family_format='pedigree')
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

    generate_study_config(dae_config, study_id, argv)
    impala_load_study(dae_config, study_id, output)

    if not argv.skip_reports:
        print("generating common reports...", file=sys.stderr)
        start = time.time()
        generate_common_report(dae_config, study_id)
        print("DONE: generating common reports in {:.2f} sec".format(
            time.time() - start
            ), file=sys.stderr)
