import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from dae.effect_annotation.effect import expand_effect_types
from dae.enrichment_tool.enrichment_utils import (
    EnrichmentEventCounts,
    get_enrichment_cache_path,
    get_enrichment_config,
)
from dae.enrichment_tool.event_counters import (
    EVENT_COUNTERS,
    EventCountersResult,
)
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("enrichment_cache_builder")


def cli(
    argv: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Generate enrichment tool cache."""
    description = "Generate enrichment tool cache"
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
            if get_enrichment_config(study) is not None:
                print(study.study_id)
    else:
        if args.studies:
            study_ids = args.studies.split(",")
        else:
            study_ids = gpf_instance.get_genotype_data_ids()

        filtered_studies = []
        for study_id in study_ids:
            study = gpf_instance.get_genotype_data(study_id)
            if get_enrichment_config(study) is not None:
                filtered_studies.append(study)
        logger.warning(
            "generating enrichment cache for studies: %s",
            [st.study_id for st in filtered_studies])

        for study in filtered_studies:
            logger.info(
                "building enrichment cache for study %s", study.study_id)
            enrichment_config = get_enrichment_config(study)
            assert enrichment_config is not None
            psc_id = enrichment_config["selected_person_set_collections"][0]
            build_enrichment_event_counts_cache(study, psc_id)


def build_enrichment_event_counts_cache(
    study: GenotypeData,
    psc_id: str,
) -> None:
    """Build enrichment event counts cache for a genotype data."""
    psc = study.get_person_set_collection(psc_id)
    assert psc is not None

    enrichment_config = get_enrichment_config(study)
    if enrichment_config is None:
        return

    assert enrichment_config is not None

    effect_groups = enrichment_config["effect_types"]
    query_effect_types = expand_effect_types(effect_groups)
    genotype_helper = GenotypeHelper(
        study, psc, effect_types=query_effect_types)
    result: EnrichmentEventCounts = {}
    for counter_id, counter in EVENT_COUNTERS.items():
        result[counter_id] = {}
        for ps_id, person_set in psc.person_sets.items():
            result[counter_id][ps_id] = {}
            for effect_group in effect_groups:
                effect_group_expanded = expand_effect_types(effect_group)
                events = counter.events(
                    genotype_helper.get_denovo_events(),
                    person_set.get_children_by_sex(),
                    effect_group_expanded)
                counts = EventCountersResult.from_events_result(events)
                result[counter_id][ps_id][effect_group] = asdict(counts)

    cache_path = get_enrichment_cache_path(study)
    Path(cache_path).write_text(json.dumps(result, indent=4))
