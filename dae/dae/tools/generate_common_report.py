import argparse
import logging
import sys
import time

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pheno.pheno_data import PhenotypeData, PhenotypeGroup, PhenotypeStudy
from dae.studies.study import GenotypeData
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("generate_common_reports")


def main(
    argv: list[str] | None = None, *,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Command line tool to generate dataset statistics."""
    description = "Generate common reports tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--show-studies",
        help="This option will print available "
        "studies and groups names",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--studies",
        help="Specify studies and groups "
        "names for generating common report. Default to all query objects.",
        default=None,
        action="store",
    )
    parser.add_argument(
        "--force",
        help="Force generation of common reports even if they are already "
        "cached.",
        default=False,
        action="store_true",
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    available_studies = [
        study.study_id for study in gpf_instance.get_all_genotype_data()
    ]
    available_pheno_studies = gpf_instance.get_phenotype_data_ids()

    if args.show_studies:
        for study_id in available_studies + available_pheno_studies:
            logger.warning("study: %s", study_id)
    else:
        elapsed = time.time() - start
        logger.info(
            "started common reports generation after %.2f sec", elapsed)
        if args.studies:
            studies = args.studies.split(",")
            logger.info("generating common reports for: %s", studies)
        else:
            studies = available_studies + available_pheno_studies
            logger.info(
                "generating common reports for all studies: %s", studies)
        for study_id in studies:
            if study_id not in available_studies + available_pheno_studies:
                logger.error("study %s not found! skipping...", study_id)
                continue

            study: GenotypeData | PhenotypeData
            if study_id in available_studies:
                study = gpf_instance.get_genotype_data(study_id)
                if study.is_remote:
                    continue
            else:
                study = gpf_instance.get_phenotype_data(study_id)
                if (
                    not isinstance(study, PhenotypeStudy)
                    and
                    not isinstance(study, PhenotypeGroup)
                ):
                    continue

            study.build_and_save(force=args.force)
