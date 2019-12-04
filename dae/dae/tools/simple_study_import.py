#!/usr/bin/env python

import os
import sys
import time
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.import_commons import construct_import_annotation_pipeline

from dae.backends.dae.loader import DenovoLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator

from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesLoader


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

    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.pedigree))

    if argv.output is None:
        output = dae_config.studies_db.dir
    else:
        output = argv.output

    print("storing results into: ", output, file=sys.stderr)
    os.makedirs(output, exist_ok=True)

    assert output is not None
    assert argv.vcf is not None or argv.denovo is not None

    pedigree_format = \
        PedigreeReader.flexible_pedigree_parse_cli_arguments(argv)

    families_loader = FamiliesLoader(
        argv.pedigree, pedigree_format=pedigree_format)

    variant_loaders = []
    if argv.denovo is not None:
        denovo_loader = DenovoLoader(
            families_loader.families,
            argv.denovo,
            genome=genome,
            params={
                'denovo_location': argv.denovo_location,
                'denovo_variant': argv.denovo_variant,
                'denovo_chrom': argv.denovo_chrom,
                'denovo_pos': argv.denovo_pos,
                'denovo_ref': argv.denovo_ref,
                'denovo_alt': argv.denovo_alt,
                'denovo_person_id': argv.denovo_person_id,
                'denovo_family_id': argv.denovo_family_id,
                'denovo_best_state': argv.denovo_best_state,
            }
        )
        denovo_loader = AnnotationPipelineDecorator(
            denovo_loader, annotation_pipeline
        )
        variant_loaders.append(denovo_loader)
    if argv.vcf is not None:
        vcf_loader = VcfLoader(
            families_loader.families,
            argv.vcf
        )
        vcf_loader = AnnotationPipelineDecorator(
            vcf_loader, annotation_pipeline
        )
        variant_loaders.append(vcf_loader)

    study_config = genotype_storage.simple_study_import(
        study_id,
        families_loader=families_loader,
        variant_loaders=variant_loaders,
        output=output
    )
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
