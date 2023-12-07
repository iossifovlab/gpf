import argparse
import logging

from typing import Optional

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gpf_instance import GPFInstance
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper


logger = logging.getLogger("enrichment_cache_builder")


def cli(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None,
) -> None:
    """Generate enrichment tool cache."""
    description = "Generate enrichment tool cache"
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
        "names for generating enrichment cache. Default to all.",
        default=None,
        action="store",
    )

    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)
    logging.getLogger("impala").setLevel(logging.WARNING)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    if args.show_studies:
        for study in gpf_instance.get_all_genotype_data():
            if EnrichmentHelper.has_enrichment_config(study):
                print(study.study_id)
    else:
        if args.studies:
            study_ids = args.studies.split(",")
        else:
            study_ids = gpf_instance.get_genotype_data_ids()

        filtered_studies = []
        for study_id in study_ids:
            study = gpf_instance.get_genotype_data(study_id)
            if EnrichmentHelper.has_enrichment_config(study):
                filtered_studies.append(study)
        logger.warning(
            "generating enrichment cache for studies: %s",
            [st.study_id for st in filtered_studies])

        enrichment_helper = EnrichmentHelper(gpf_instance.grr)
        for study in filtered_studies:
            logger.info(
                "building enrichment cache for study %s", study.study_id)
            enrichment_config = enrichment_helper.get_enrichment_config(study)
            assert enrichment_config is not None
            psc_id = enrichment_config["selected_person_set_collections"][0]
            enrichment_helper.build_enrichment_event_counts_cache(
                study, psc_id)
