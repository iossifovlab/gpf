import logging

from typing import Optional, cast, Iterable, Union

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.effect_annotation.effect import expand_effect_types
from dae.studies.study import GenotypeData
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground, EnrichmentResult
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
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
        counter_klass = EVENT_COUNTERS[counter_id]
        counter = counter_klass()
        return counter

    # def create_enrichment_tool(
    #     self, genotype_data: GenotypeData,
    #     background_id: Optional[str] = None,
    #     counter_id: Optional[str] = None
    # ) -> EnrichmentTool:
    #     """Create enrichment tool for a genotype data."""
    #     if not self.has_enrichment_config(genotype_data):
    #         raise ValueError(
    #             f"no enrichment config for study "
    #             f"{genotype_data.study_id}")
    #     enrichment_config = self.get_enrichment_config(genotype_data)
    #     assert enrichment_config is not None
    #     if background_id is None:
    #         background_id = enrichment_config["default_background_model"]
    #     if counter_id is None:
    #         counter_id = enrichment_config["default_counting_model"]

    #     background = self.create_background(background_id)
    #     counter = self.create_counter(counter_id)
    #     return EnrichmentTool(background, counter)

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
        if background_id is None:
            background_id = enrichment_config["default_background_model"]
        if counter_id is None:
            counter_id = enrichment_config["default_counting_model"]

        background = self.create_background(background_id)
        counter = self.create_counter(counter_id)

        psc = study.get_person_set_collection(psc_id)
        assert psc is not None

        query_effect_types = expand_effect_types(effect_groups)
        genotype_helper = GenotypeHelper(
            study, psc, effect_types=query_effect_types)

        results: dict[str, dict[str, EnrichmentResult]] = {}
        for ps_id, person_set in psc.person_sets.items():
            children_stats = person_set.get_children_stats()
            if children_stats.total <= 0:
                continue
            results[ps_id] = {}
            for effect_group in effect_groups:
                effect_group_expanded = expand_effect_types([effect_group])
                events = counter.events(
                    genotype_helper.get_denovo_events(),
                    person_set.get_children_by_sex(),
                    effect_group_expanded)
                event_counts = EventCountersResult.from_events_result(events)
                overlapped_counts = overlap_event_counts(events, gene_syms)

                result = background.calc_enrichment_test(
                    event_counts, overlapped_counts,
                    gene_syms, effect_types=effect_group)
                if isinstance(effect_group, str):
                    eg_id = effect_group
                else:
                    eg_id = ",".join(effect_group)
                results[ps_id][eg_id] = result

        return results
