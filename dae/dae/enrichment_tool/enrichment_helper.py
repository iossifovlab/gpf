import os
import logging
import json

from dataclasses import asdict
from typing import Optional, cast, Iterable, Union

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.effect_annotation.effect import expand_effect_types
from dae.studies.study import GenotypeData
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground, EnrichmentResult
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground, GeneScoreEnrichmentBackground
from dae.enrichment_tool.samocha_background import \
    SamochaEnrichmentBackground
from dae.enrichment_tool.event_counters import EVENT_COUNTERS, CounterBase, \
    overlap_event_counts, EventCountersResult
# from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.genotype_helper import GenotypeHelper

logger = logging.getLogger(__name__)


class EnrichmentHelper:
    """Helper class to create enrichment tool for a genotype data."""

    _BACKGROUNDS_CACHE: dict[str, BaseEnrichmentBackground] = {}

    def __init__(self, grr: GenomicResourceRepo):
        self.grr = grr

    @staticmethod
    def get_enrichment_config(
        genotype_data: GenotypeData
    ) -> Optional[Box]:
        return cast(
            Optional[Box],
            genotype_data.config.get("enrichment")
        )

    @staticmethod
    def has_enrichment_config(genotype_data: GenotypeData) -> bool:
        return EnrichmentHelper\
            .get_enrichment_config(genotype_data) is not None

    def collect_genotype_data_backgrounds(
        self, genotype_data: GenotypeData
    ) -> list[BaseEnrichmentBackground]:
        """Collect enrichment backgrounds configured for a genotype data."""
        if not self.has_enrichment_config(genotype_data):
            return []
        enrichment_config = self.get_enrichment_config(genotype_data)
        assert enrichment_config is not None

        result = []
        for background_id in enrichment_config["selected_background_models"]:
            result.append(self.create_background(background_id))
        return result

    def _build_background_from_resource(
        self, resource_id: str
    ) -> BaseEnrichmentBackground:
        resource = self.grr.get_resource(resource_id)
        if resource.get_type() == "gene_weights_enrichment_background":
            return GeneWeightsEnrichmentBackground(resource)

        if resource.get_type() == "gene_score":
            return GeneScoreEnrichmentBackground(resource)

        if resource.get_type() == "samocha_enrichment_background":
            return SamochaEnrichmentBackground(resource)

        raise ValueError(
            f"unexpected resource type <{resource.get_type()}> "
            f"of resource <{resource.resource_id}> "
            f"for enrichment backgound"
        )

    def create_background(
        self, background_id: str
    ) -> BaseEnrichmentBackground:
        """Construct and return an enrichment background."""
        if background_id in self._BACKGROUNDS_CACHE:
            return self._BACKGROUNDS_CACHE[background_id]

        background = self._build_background_from_resource(background_id)
        background.load()

        self._BACKGROUNDS_CACHE[background_id] = background
        return background

    def create_counter(self, counter_id: str) -> CounterBase:
        """Create counter for a genotype data."""
        return EVENT_COUNTERS[counter_id]

    def calc_enrichment_test(
        self,
        study: GenotypeData,
        psc_id: str,
        gene_syms: Iterable[str],
        effect_groups: Union[Iterable[str], Iterable[Iterable[str]]],
        background_id: Optional[str] = None,
        counter_id: Optional[str] = None
    ) -> dict[str, dict[str, EnrichmentResult]]:
        """Perform enrichment test for a genotype data."""
        if not self.has_enrichment_config(study):
            raise ValueError(
                f"no enrichment config for study "
                f"{study.study_id}")
        enrichment_config = self.get_enrichment_config(study)
        assert enrichment_config is not None
        if background_id is None or not background_id:
            background_id = enrichment_config["default_background_model"]
        if counter_id is None or not counter_id:
            counter_id = enrichment_config["default_counting_model"]

        assert background_id is not None, enrichment_config
        assert counter_id is not None, enrichment_config

        background = self.create_background(background_id)
        counter = self.create_counter(counter_id)

        event_counters_cache: Optional[
            dict[str, dict[str, dict[str, dict[str, int]]]]] = None
        if self._has_enrichment_cache(study):
            event_counters_cache = \
                self._load_enrichment_event_counts_cache(study)

        psc = study.get_person_set_collection(psc_id)
        assert psc is not None

        query_effect_types = expand_effect_types(effect_groups)
        gene_syms_query: Optional[list[str]] = None
        if event_counters_cache is not None:
            gene_syms_query = list(gene_syms)
        genotype_helper = GenotypeHelper(
            study, psc,
            effect_types=query_effect_types,
            genes=gene_syms_query)

        results: dict[str, dict[str, EnrichmentResult]] = {}
        for ps_id, person_set in psc.person_sets.items():
            children_stats = person_set.get_children_stats()
            if children_stats.total <= 0:
                continue

            results[ps_id] = {}
            for effect_group in effect_groups:
                effect_group_expanded = expand_effect_types([effect_group])
                if isinstance(effect_group, str):
                    eg_id = effect_group
                else:
                    eg_id = ",".join(effect_group)

                events = counter.events(
                    genotype_helper.get_denovo_events(),
                    person_set.get_children_by_sex(),
                    effect_group_expanded)
                if event_counters_cache is not None:
                    cache = \
                        event_counters_cache[counter_id][ps_id][eg_id]
                    event_counts = EventCountersResult(**cache)  # type: ignore
                else:
                    event_counts = \
                        EventCountersResult.from_events_result(events)
                overlapped_counts = overlap_event_counts(events, gene_syms)

                result = background.calc_enrichment_test(
                    event_counts, overlapped_counts,
                    gene_syms, effect_types=[effect_group],
                    children_stats=children_stats)
                results[ps_id][eg_id] = result

        return results

    def _enrichment_cache_path(self, study: GenotypeData) -> str:
        return os.path.join(study.config_dir, "enrichment_cache.json")

    def _has_enrichment_cache(self, study: GenotypeData) -> bool:
        cache_path = self._enrichment_cache_path(study)
        return os.path.exists(cache_path)

    def _load_enrichment_event_counts_cache(
        self, study: GenotypeData
    ) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
        cache_path = self._enrichment_cache_path(study)
        with open(cache_path, "r") as cache_file:
            return cast(
                dict[str, dict[str, dict[str, dict[str, int]]]],
                json.loads(cache_file.read())
            )

    def build_enrichment_event_counts_cache(
        self, study: GenotypeData,
        psc_id: str
    ) -> None:
        """Build enrichment event counts cache for a genotype data."""
        psc = study.get_person_set_collection(psc_id)
        assert psc is not None

        enrichment_config = self.get_enrichment_config(study)
        if enrichment_config is None:
            return

        assert enrichment_config is not None

        effect_groups = enrichment_config["effect_types"]
        query_effect_types = expand_effect_types(effect_groups)
        genotype_helper = GenotypeHelper(
            study, psc, effect_types=query_effect_types)
        result: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
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

        cache_path = self._enrichment_cache_path(study)
        with open(cache_path, "w") as cache_file:
            cache_file.write(json.dumps(result, indent=4))
