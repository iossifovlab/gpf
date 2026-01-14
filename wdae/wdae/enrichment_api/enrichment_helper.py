import json
import logging
import os
from abc import abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar, cast

from dae.effect_annotation.effect import expand_effect_types
from dae.enrichment_tool.base_enrichment_background import (
    BaseEnrichmentBackground,
    EnrichmentResult,
)
from dae.enrichment_tool.enrichment_utils import (
    EnrichmentEventCounts,
)
from dae.enrichment_tool.event_counters import (
    EVENT_COUNTERS,
    CounterBase,
    EventCountersResult,
    overlap_event_counts,
)
from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
    GeneWeightsEnrichmentBackground,
)
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
    parse_resource_id_version,
)
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy

logger = logging.getLogger(__name__)


class BaseEnrichmentHelper(GPFTool):
    """Base helper class to create enrichment helper WDAE study."""

    def __init__(self) -> None:
        super().__init__("enrichment_helper")

    @abstractmethod
    def get_enrichment_models(self) -> dict[str, Any]:
        """Return enrichment models available for the study."""


class EnrichmentHelper(BaseEnrichmentHelper):
    """Helper Base helper class to create enrichment helper WDAE study."""

    _BACKGROUNDS_CACHE: ClassVar[dict[str, BaseEnrichmentBackground]] = {}

    def __init__(
        self,
        grr: GenomicResourceRepo,
        study: WDAEStudy,
    ):
        super().__init__()
        self.grr = grr
        self.study = study

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError

    def get_enrichment_models(self) -> dict[str, Any]:
        """Return enrichment models available for the study."""

        background_descriptions = [
            {
                "id": background.background_id,
                "name": background.name,
                "type": background.background_type,
                "summary": background.resource.get_summary(),
                "desc": background.resource.get_description(),
            }
            for background in self.collect_genotype_data_backgrounds()
        ]

        counting_models = []
        if self.study.enrichment_config is not None:
            counting_models = [
                {
                    "id": counting_model.id,
                    "name": counting_model.name,
                    "desc": counting_model.desc,
                }
                for counting_model in dict(
                    self.study.enrichment_config["counting"],
                ).values()
                if counting_model.id in self.get_selected_counting_models()
            ]

        return {
            "background": background_descriptions,
            "counting": counting_models,
            "defaultBackground": self.get_default_background_model(),
            "defaultCounting": self.get_default_counting_model(),
        }

    def get_default_background_model(self) -> str:
        """
        Return default background model field from the enrichment config.
        If it is missing, default to the first selected background model.
        """
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None
        background_id: str
        if enrichment_config["default_background_model"]:
            background_id = str(
                enrichment_config["default_background_model"])
        else:
            background_id = str(
                enrichment_config["selected_background_models"][0])
        resource_id, _ = parse_resource_id_version(background_id)
        return resource_id

    def get_default_counting_model(self) -> str:
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None
        return str(enrichment_config["default_counting_model"])

    def get_selected_counting_models(self) -> list[str]:
        """
        Return selected counting models field from the enrichment config.
        If it is missing, default to the counting field.
        """
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None

        if enrichment_config["selected_counting_models"]:
            return cast(
                list[str],
                enrichment_config["selected_counting_models"],
            )
        return list(enrichment_config["counting"].keys())

    def get_selected_person_set_collections(self) -> str:
        """
        Return selected person set collections field from the enrichment config.
        If it is missing, default to the first available person set collection
        in the provided study.
        """
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None

        if enrichment_config["selected_person_set_collections"]:
            return str(enrichment_config["selected_person_set_collections"][0])
        return next(iter(
            self.study.genotype_data.person_set_collections.keys(),
        ))

    def collect_genotype_data_backgrounds(
        self,
    ) -> list[BaseEnrichmentBackground]:
        """Collect enrichment backgrounds configured for a genotype data."""
        if self.study.enrichment_config is None:
            return []
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None

        return [
            self.create_background(background_id)
            for background_id in enrichment_config["selected_background_models"]
        ]

    def _build_background_from_resource(
        self, resource_id: str,
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
            f"for enrichment backgound",
        )

    def create_background(
        self, background_id: str,
    ) -> BaseEnrichmentBackground:
        """Construct and return an enrichment background."""
        resource_id, _ = parse_resource_id_version(background_id)
        if resource_id in self._BACKGROUNDS_CACHE:
            return self._BACKGROUNDS_CACHE[resource_id]

        background = self._build_background_from_resource(background_id)
        background.load()

        self._BACKGROUNDS_CACHE[background.resource_id] = background
        return background

    def create_counter(self, counter_id: str) -> CounterBase:
        """Create counter for a genotype data."""
        return EVENT_COUNTERS[counter_id]

    def calc_enrichment_test(
        self,
        psc_id: str,
        gene_syms: Iterable[str],
        effect_groups: Iterable[str] | Iterable[Iterable[str]],
        background_id: str | None = None,
        counter_id: str | None = None,
    ) -> dict[str, dict[str, EnrichmentResult]]:
        """Perform enrichment test for a genotype data."""
        if self.study.enrichment_config is None:
            raise ValueError(
                f"no enrichment config for study "
                f"{self.study.study_id}")
        enrichment_config = self.study.enrichment_config
        assert enrichment_config is not None
        if background_id is None or not background_id:
            background_id = enrichment_config["default_background_model"]
        if counter_id is None or not counter_id:
            counter_id = enrichment_config["default_counting_model"]

        assert background_id is not None, enrichment_config
        assert counter_id is not None, enrichment_config

        background = self.create_background(background_id)
        counter = self.create_counter(counter_id)

        event_counters_cache: EnrichmentEventCounts | None = None
        if self._has_enrichment_cache():
            event_counters_cache = \
                self._load_enrichment_event_counts_cache()

        psc = self.study.get_person_set_collection(psc_id)
        assert psc is not None

        query_effect_types = expand_effect_types(effect_groups)
        gene_syms_query: list[str] | None = None
        if event_counters_cache is not None:
            gene_syms_query = list(gene_syms)
        genotype_helper = GenotypeHelper(
            self.study.genotype_data, psc,
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

    def _has_enrichment_cache(self) -> bool:
        cache_path = self.study.enrichment_cache_path
        if cache_path is None:
            return False
        return os.path.exists(cache_path)

    def _load_enrichment_event_counts_cache(
        self,
    ) -> EnrichmentEventCounts | None:
        cache_path = self.study.enrichment_cache_path
        if cache_path is None:
            return None
        return cast(
            EnrichmentEventCounts,
            json.loads(Path(cache_path).read_text()),
        )
