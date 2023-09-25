#!/usr/bin/env python
import sys
import time
import argparse
import logging
import os
import json

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.common_reports.common_report import CommonReport
from dae.pedigrees.loader import FamiliesLoader

logger = logging.getLogger("generate_common_reports")


def main(argv, gpf_instance=None):
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

            if study.is_group:
                logger.info("%s is group, caching families...", study_id)
                try:
                    path = os.path.join(
                        study.config["conf_dir"], "families_cache.ped"
                    )
                    FamiliesLoader.save_families(study.families, path)
                    logger.info(
                        "Done writing %s families data into %s", study_id, path
                    )
                except BaseException:  # pylint: disable=broad-except
                    logger.exception(
                        "Failed to cache families for %s", study_id
                    )

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


if __name__ == "__main__":
    main(sys.argv[1:])
