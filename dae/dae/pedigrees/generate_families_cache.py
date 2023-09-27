import sys
import time
import argparse
import logging
from typing import Optional, cast

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.studies.study import GenotypeDataGroup
from dae.gpf_instance.gpf_instance import GPFInstance


logger = logging.getLogger("generate_families_cache")


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    """Command line tool to create genotype groups families cache."""
    description = "Create genotype groups families cache"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_argumnets(parser)

    parser.add_argument(
        "--show-groups",
        help="This option will print available "
        "genotype groups IDs",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--groups",
        help="Specify genotype groups "
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

    available_studies = gpf_instance.get_all_genotype_data()
    elapsed = time.time() - start
    logger.info(
        "GPF instance genotype data loaded %.2f sec", elapsed)

    if args.show_groups:
        for study in available_studies:
            if not study.is_group:
                continue
            logger.warning("genotype group: %s", study.study_id)
        return

    start = time.time()

    studies = []
    if args.studies:
        study_ids = args.studies.split(",")
        all_study_ids = set(gpf_instance.get_genotype_data_ids())
        for study_id in study_ids:
            if study_id not in all_study_ids:
                logger.warning(
                    "study %s not found in GPF instance studies %s",
                    study_id, all_study_ids)
                continue
            study = gpf_instance.get_genotype_data(study_id)
            if not study.is_group:
                logger.warning(
                    "study %s is not a genotype data group; skipping",
                    study_id)
                continue
            studies.append(study)
        study_ids = set(st.study_id for st in studies)
        logger.info("build families data cache for: %s", study_ids)
    else:
        for study in available_studies:
            if study.is_group:
                studies.append(study)
        study_ids = set(st.study_id for st in studies)
        logger.info(
            "build families data cache for all groups: %s!!!",
            study_ids)

    for study in studies:
        study_group = cast(GenotypeDataGroup, study)
        logger.info("%s is a group, caching families...", study_group.study_id)
        if study_group.load_families():
            study_group.build_families()
        study_group.save_cached_families()
        study_group.save_cached_person_sets()

    logger.info(
        "generate families cache for %s genotype groups elapsed %.2f sec",
        study_ids, elapsed)
