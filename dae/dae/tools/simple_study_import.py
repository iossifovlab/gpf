#!/usr/bin/env python

import os
import sys
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.backends.impala.import_commons import (
    construct_import_annotation_pipeline,
    construct_import_effect_annotator,
    save_study_config,
)

from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.backends.vcf.loader import VcfLoader

from dae.backends.cnv.loader import CNVLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator, \
    EffectAnnotationDecorator

from dae.pedigrees.loader import FamiliesLoader

from dae.tools import generate_common_report

logger = logging.getLogger("simple_study_import")


def cli_arguments(dae_config, argv=sys.argv[1:]):
    if dae_config:
        default_genotype_storage_id = dae_config.genotype_storage.default
    else:
        default_genotype_storage_id = None

    parser = argparse.ArgumentParser(
        description="simple import of new study data",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--verbose', '-V', action='count', default=0)

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

    parser.add_argument(
        "--force", "-F",
        dest="force",
        action="store_true",
        help="allows overwriting configuration file in case "
        "target directory already contains such file",
        default=False
    )

    DenovoLoader.cli_arguments(parser, options_only=True)
    VcfLoader.cli_arguments(parser, options_only=True)
    DaeTransmittedLoader.cli_arguments(parser, options_only=True)
    CNVLoader.cli_arguments(parser, options_only=True)

    parser_args = parser.parse_args(argv)
    return parser_args


def generate_denovo_gene_sets(gpf_instance, study_id):
    from dae.tools.generate_denovo_gene_sets import main

    argv = ["--studies", study_id]
    main(gpf_instance=gpf_instance, argv=argv)


def _decorate_loader(variants_loader, effect_annotator, annotation_pipeline):
    variants_loader = EffectAnnotationDecorator(
        variants_loader, effect_annotator)

    if annotation_pipeline is not None:
        variants_loader = AnnotationPipelineDecorator(
            variants_loader, annotation_pipeline)

    return variants_loader


def main(argv, gpf_instance=None):
    dae_config = None
    if gpf_instance is not None:
        dae_config = gpf_instance.dae_config
    else:
        try:
            gpf_instance = GPFInstance()
            dae_config = gpf_instance.dae_config
        except Exception as e:
            logger.warning("GPF not configured correctly")
            logger.exception(e)

    argv = cli_arguments(dae_config, argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger("impala").setLevel(logging.WARNING)

    genotype_storage_factory = gpf_instance.genotype_storage_db
    genome = gpf_instance.reference_genome

    genotype_storage = genotype_storage_factory.get_genotype_storage(
        argv.genotype_storage
    )
    logger.debug(
        f"genotype storage: {argv.genotype_storage}, {genotype_storage}")
    assert genotype_storage is not None, argv.genotype_storage

    annotation_pipeline = construct_import_annotation_pipeline(gpf_instance)
    effect_annotator = construct_import_effect_annotator(gpf_instance)

    if argv.id is not None:
        study_id = argv.id
    else:
        study_id, _ = os.path.splitext(os.path.basename(argv.families))

    if argv.output is None:
        from pprint import pprint
        pprint(dae_config)
        output = dae_config.studies.dir
    else:
        output = argv.output

    logger.info(f"storing results into: {output}")
    os.makedirs(output, exist_ok=True)

    assert output is not None

    start = time.time()
    families_filename, families_params = FamiliesLoader.parse_cli_arguments(
        argv
    )
    families_loader = FamiliesLoader(families_filename, **families_params)
    families = families_loader.load()
    elapsed = time.time() - start
    logger.info(f"Families loaded in {elapsed:.2f} sec")
    logger.debug(f"{families.ped_df.head()}")

    variant_loaders = []
    if argv.denovo_file is not None:
        denovo_filename, denovo_params = DenovoLoader.parse_cli_arguments(argv)
        denovo_loader = DenovoLoader(
            families, denovo_filename, genome=genome, params=denovo_params
        )

        denovo_loader = _decorate_loader(
            denovo_loader, effect_annotator, annotation_pipeline
        )
        variant_loaders.append(denovo_loader)

    if argv.cnv_file is not None:
        cnv_filename, cnv_params = CNVLoader.parse_cli_arguments(argv)
        cnv_loader = CNVLoader(
            families, cnv_filename, genome=genome, params=cnv_params
        )
        cnv_loader = _decorate_loader(
            cnv_loader, effect_annotator, annotation_pipeline)
        variant_loaders.append(cnv_loader)

    if argv.vcf_files is not None:
        vcf_files, vcf_params = VcfLoader.parse_cli_arguments(argv)
        vcf_loader = VcfLoader(families, vcf_files, genome, params=vcf_params)
        vcf_loader = _decorate_loader(
            vcf_loader, effect_annotator, annotation_pipeline)

        variant_loaders.append(vcf_loader)

    if argv.dae_summary_file is not None:
        dae_files, dae_params = DaeTransmittedLoader.parse_cli_arguments(argv)
        dae_loader = DaeTransmittedLoader(
            families, dae_files, genome, params=dae_params
        )
        dae_loader = _decorate_loader(
            dae_loader, effect_annotator, annotation_pipeline)
        variant_loaders.append(dae_loader)

    study_config = genotype_storage.simple_study_import(
        study_id,
        families_loader=families_loader,
        variant_loaders=variant_loaders,
        output=output,
        study_config=argv.study_config,
    )
    save_study_config(
        dae_config, study_id, study_config, force=argv.force)

    if not argv.skip_reports:
        # needs to reload the configuration, hence gpf_instance=None
        gpf_instance.reload()

        print("generating common reports...")
        start = time.time()
        argv = ["--studies", study_id]
        generate_common_report.main(argv, gpf_instance)

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
