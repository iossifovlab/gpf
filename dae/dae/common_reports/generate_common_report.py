import sys
import time
import argparse
import logging
import os
import json
from typing import Optional

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.common_reports.common_report import CommonReport

logger = logging.getLogger("generate_common_reports")


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    """Command line tool to generate dataset statistics."""
    description = "Generate common reports tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_argumnets(parser)

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

    available_studies = gpf_instance.get_genotype_data_ids(local_only=True)

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

            if not study.config.common_report or \
                    not study.config.common_report.enabled:
                logger.warning(
                    "skipping study %s since common report is disabled",
                    study.study_id)
                continue

            common_report = CommonReport.build_report(study)
            file_path = study.config.common_report.file_path

            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "w+", encoding="utf8") as crf:
                json.dump(common_report.to_dict(full=True), crf)
