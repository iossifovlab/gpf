#!/usr/bin/env python

import os
import sys
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.import_tools.import_tools import ImportProject
from dae.import_tools.cli import run_with_project

from dae.variants_loaders.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.variants_loaders.vcf.loader import VcfLoader

from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator, \
    EffectAnnotationDecorator

from dae.pedigrees.loader import FamiliesLoader

from dae.tools import generate_common_report
from dae.tools import generate_denovo_gene_sets

from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("simple_study_import")


def cli_arguments(dae_config, argv=None):
    """Create and return CLI arguments parser."""
    default_genotype_storage_id = None
    if dae_config and dae_config.genotype_storage:
        default_genotype_storage_id = \
            dae_config.genotype_storage.default

    parser = argparse.ArgumentParser(
        description="simple import of new study data",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    VerbosityConfiguration.set_argumnets(parser)
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

    # parser.add_argument(
    #     "--study-config",
    #     type=str,
    #     default=None,
    #     dest="study_config",
    #     help="Config used to overwrite values in generated configuration",
    # )

    # parser.add_argument(
    #     "--force", "-F",
    #     dest="force",
    #     action="store_true",
    #     help="allows overwriting configuration file in case "
    #     "target directory already contains such file",
    #     default=False
    # )

    DenovoLoader.cli_arguments(parser, options_only=True)
    VcfLoader.cli_arguments(parser, options_only=True)
    DaeTransmittedLoader.cli_arguments(parser, options_only=True)
    CNVLoader.cli_arguments(parser, options_only=True)

    parser_args = parser.parse_args(argv or sys.argv[1:])
    return parser_args


def _decorate_loader(variants_loader, effect_annotator, annotation_pipeline):
    variants_loader = EffectAnnotationDecorator(
        variants_loader, effect_annotator)

    if annotation_pipeline is not None:
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline)

    return variants_loader


def build_import_project(argv, gpf_instance):
    """Build an import project based on the CLI arguments."""
    project = {
        "gpf_instance": {
            "path": gpf_instance.dae_config.conf_dir,
        },
        "destination": {
            "storage_id": argv.genotype_storage
        }
    }

    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.families))
    project["id"] = study_id

    if argv.output is not None:
        project["processing_config"] = {}
        project["processing_config"]["work_dir"] = argv.output

    project["input"] = {}

    families_filename, families_params = \
        FamiliesLoader.parse_cli_arguments(argv)
    project["input"]["pedigree"] = \
        ImportProject.del_loader_prefix(families_params, "ped_")
    project["input"]["pedigree"]["file"] = families_filename

    if argv.denovo_file is not None:
        denovo_filename, denovo_params = DenovoLoader.parse_cli_arguments(argv)
        project["input"]["denovo"] = \
            ImportProject.del_loader_prefix(denovo_params, "denovo_")
        project["input"]["denovo"]["files"] = [denovo_filename]

    if argv.cnv_file is not None:
        cnv_filename, cnv_params = CNVLoader.parse_cli_arguments(argv)
        project["input"]["cnv"] = \
            ImportProject.del_loader_prefix(cnv_params, "cnv_")
        project["input"]["cnv"]["files"] = [cnv_filename]

    if argv.vcf_files is not None:
        vcf_files, vcf_params = VcfLoader.parse_cli_arguments(argv)
        project["input"]["vcf"] = \
            ImportProject.del_loader_prefix(vcf_params, "vcf_")
        project["input"]["vcf"]["files"] = vcf_files

    if argv.dae_summary_file is not None:
        dae_file, dae_params = DaeTransmittedLoader.parse_cli_arguments(argv)
        project["input"]["dae"] = \
            ImportProject.del_loader_prefix(dae_params, "dae_")
        project["input"]["dae"]["files"] = [dae_file]

    return ImportProject.build_from_config(project, gpf_instance=gpf_instance)


def main(argv, gpf_instance=None):
    """Run the simple study import procedure."""
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    dae_config = None
    if gpf_instance is not None:
        dae_config = gpf_instance.dae_config
    else:
        try:
            gpf_instance = GPFInstance.build()
            dae_config = gpf_instance.dae_config
        except Exception:  # pylint: disable=broad-except
            logger.warning("GPF not configured correctly", exc_info=True)

    argv = cli_arguments(dae_config, argv)
    VerbosityConfiguration.set(argv)
    logging.getLogger("impala").setLevel(logging.WARNING)

    import_project = build_import_project(argv, gpf_instance=gpf_instance)
    run_with_project(import_project)

    if not argv.skip_reports:
        # needs to reload the configuration, hence gpf_instance=None
        gpf_instance.reload()
        argv = ["--studies", import_project.study_id]

        logger.info("generating common reports...")
        start = time.time()
        generate_common_report.main(argv, gpf_instance)
        logger.info(
            "DONE: generating common reports in %.2f sec",
            time.time() - start)

        logger.info("generating de Novo gene sets...")
        start = time.time()
        generate_denovo_gene_sets.main(gpf_instance=gpf_instance, argv=argv)
        logger.info(
            "DONE: generating de Novo gene sets in %.2f sec",
            time.time() - start)


if __name__ == "__main__":
    main(sys.argv[1:])
