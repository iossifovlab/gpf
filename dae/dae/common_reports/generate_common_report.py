#!/usr/bin/env python

import argparse
import logging
import sys
import time

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("generate_common_reports")


def main(
    argv: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Command line tool to generate dataset statistics."""
    description = "Generate common reports tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--show-studies",
        help="This option will print available "
        "genotype studies and groups names",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--studies",
        help="Specify genotype studies and groups "
        "names for generating common report. Default to all query objects.",
        default=None,
        action="store",
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    available_studies = gpf_instance.get_genotype_data_ids()

    if args.show_studies:
        for study_id in available_studies:
            logger.warning("study: %s", study_id)
    else:
        elapsed = time.time() - start
        logger.info(
            "started common reports generation after %.2f sec", elapsed)
        if args.studies:
            studies = args.studies.split(",")
            logger.info("generating common reports for: %s", studies)
        else:
            logger.info("generating common reports for all studies!!!")
            studies = available_studies
        for study_id in studies:
            if study_id not in available_studies:
                logger.error("study %s not found! skipping...", study_id)
                continue

            study = gpf_instance.get_genotype_data(study_id)

            study.build_and_save()
