#!/usr/bin/env python

import os
import sys
import time
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.impala.import_commons import (
    construct_import_annotation_pipeline,
    save_study_config,
)

from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.raw.loader import (
    AnnotationPipelineDecorator,
    AlleleFrequencyDecorator,
)
from dae.backends.cnv.loader import CNVLoader

from dae.pedigrees.loader import FamiliesLoader


def cli_arguments(dae_config, argv=sys.argv[1:]):
    default_genotype_storage_id = dae_config.genotype_storage.default

    parser = argparse.ArgumentParser(
        description="simple import of new study data",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    FamiliesLoader.cli_arguments(parser)

    parser.add_argument(
        "--id",
        "--study-id",
        type=str,
        metavar="<study ID>",
        dest="id",
        help="Unique study ID to use. "
        "If not specified the basename of the family pedigree file is used "
        "for study ID",
    )

    parser.add_argument(
        "--vcf-files",
        type=str,
        nargs="+",
        metavar="<VCF filename>",
        help="VCF file to import",
    )

    parser.add_argument(
        "--denovo-file",
        type=str,
        metavar="<de Novo variants filename>",
        help="DAE denovo variants file",
    )

    parser.add_argument(
        "--cnv-file",
        type=str,
        metavar="<CNV variants filename>",
        help="CNV variants file",
    )

    parser.add_argument(
        "--dae-summary-file",
        type=str,
        metavar="<summary filename>",
        help="DAE transmitted summary variants file to import",
    )

    parser.add_argument(
        "-o",
        "--out",
        type=str,
        default=None,
        dest="output",
        metavar="<output directory>",
        help="output directory for storing intermediate parquet files. "
        'If none specified, "parquet/" directory inside GPF instance '
        "study directory is used [default: %(default)s]",
    )

    parser.add_argument(
        "--skip-reports",
        help="skip running report generation [default: %(default)s]",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--genotype-storage",
        "--gs",
        type=str,
        metavar="<genotype storage id>",
        dest="genotype_storage",
        help="Id of defined in DAE.conf genotype storage "
        "[default: %(default)s]",
        default=default_genotype_storage_id,
        action="store",
    )

    parser.add_argument(
        "--add-chrom-prefix",
        type=str,
        default=None,
        help="Add specified prefix to each chromosome name in "
        "variants file",
    )

    parser.add_argument(
        "--study-config",
        type=str,
        default=None,
        dest="study_config",
        help="Config used to overwrite values in generated configuration",
    )

    DenovoLoader.cli_options(parser)
    VcfLoader.cli_options(parser)
    DaeTransmittedLoader.cli_options(parser)
    CNVLoader.cli_options(parser)

    parser_args = parser.parse_args(argv)
    return parser_args


def generate_common_report(gpf_instance, study_id):
    from dae.tools.generate_common_report import main

    argv = ["--studies", study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def generate_denovo_gene_sets(gpf_instance, study_id):
    from dae.tools.generate_denovo_gene_sets import main

    argv = ["--studies", study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def main(argv, gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    dae_config = gpf_instance.dae_config

    argv = cli_arguments(dae_config, argv)

    genotype_storage_factory = gpf_instance.genotype_storage_db
    genomes_db = gpf_instance.genomes_db
    genome = genomes_db.get_genome()

    genotype_storage = genotype_storage_factory.get_genotype_storage(
        argv.genotype_storage
    )
    print("genotype storage:", argv.genotype_storage, genotype_storage)
    assert genotype_storage is not None, argv.genotype_storage

    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance, annotation_configfile=None
    )

    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.families))

    if argv.output is None:
        output = dae_config.studies_db.dir
    else:
        output = argv.output

    print("storing results into: ", output, file=sys.stderr)
    os.makedirs(output, exist_ok=True)

    assert output is not None
    # assert argv.vcf_files is not None or argv.denovo_file is not None

    start = time.time()
    families_filename, families_params = FamiliesLoader.parse_cli_arguments(
        argv
    )
    families_loader = FamiliesLoader(families_filename, params=families_params)
    families = families_loader.load()
    elapsed = time.time() - start
    print(f"Families loaded in in {elapsed:.2f} sec", file=sys.stderr)

    variant_loaders = []
    if argv.denovo_file is not None:
        denovo_filename, denovo_params = DenovoLoader.parse_cli_arguments(argv)
        denovo_loader = DenovoLoader(
            families, denovo_filename, genome=genome, params=denovo_params
        )
        denovo_loader = AnnotationPipelineDecorator(
            denovo_loader, annotation_pipeline
        )
        variant_loaders.append(denovo_loader)

    if argv.cnv_file is not None:
        cnv_filename, cnv_params = CNVLoader.parse_cli_arguments(argv)
        cnv_loader = CNVLoader(
            families, cnv_filename, genome=genome, params=cnv_params
        )
        # TODO: Annotate
        variant_loaders.append(cnv_loader)

    if argv.vcf_files is not None:
        vcf_files, vcf_params = VcfLoader.parse_cli_arguments(argv)
        vcf_loader = VcfLoader(families, vcf_files, genome, params=vcf_params)
        vcf_loader = AnnotationPipelineDecorator(
            vcf_loader, annotation_pipeline
        )
        vcf_loader = AlleleFrequencyDecorator(vcf_loader)

        variant_loaders.append(vcf_loader)

    if argv.dae_summary_file is not None:
        dae_files, dae_params = DaeTransmittedLoader.parse_cli_arguments(argv)
        dae_loader = DaeTransmittedLoader(
            families, dae_files, genome, params=dae_params
        )
        dae_loader = AnnotationPipelineDecorator(
            dae_loader, annotation_pipeline
        )
        variant_loaders.append(dae_loader)

    study_config = genotype_storage.simple_study_import(
        study_id,
        families_loader=families_loader,
        variant_loaders=variant_loaders,
        output=output,
        study_config=argv.study_config,
    )
    save_study_config(dae_config, study_id, study_config)

    if not argv.skip_reports:
        # needs to reload the configuration, hence gpf_instance=None
        gpf_instance.reload()

        print("generating common reports...", file=sys.stderr)
        start = time.time()
        generate_common_report(gpf_instance, study_id)
        print(
            "DONE: generating common reports in {:.2f} sec".format(
                time.time() - start
            ),
            file=sys.stderr,
        )

        print("generating de Novo gene sets...", file=sys.stderr)
        start = time.time()
        generate_denovo_gene_sets(gpf_instance, study_id)
        print(
            "DONE: generating de Novo gene sets in {:.2f} sec".format(
                time.time() - start
            ),
            file=sys.stderr,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
