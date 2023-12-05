import logging

from typing import Optional, cast

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.studies.study import GenotypeData
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.enrichment_tool.samocha_background import \
    SamochaEnrichmentBackground
from dae.enrichment_tool.event_counters import EVENT_COUNTERS, CounterBase
from dae.enrichment_tool.tool import EnrichmentTool

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
        self._BACKGROUNDS_CACHE[background_id] = background
        return background

    def create_counter(self, counter_id: str) -> CounterBase:
        """Create counter for a genotype data."""
        counter_klass = EVENT_COUNTERS[counter_id]
        counter = counter_klass()
        return counter

    def create_enrichment_tool(
        self, genotype_data: GenotypeData,
        background_id: Optional[str] = None,
        counter_id: Optional[str] = None
    ) -> EnrichmentTool:
        """Create enrichment tool for a genotype data."""
        if not self.has_enrichment_config(genotype_data):
            raise ValueError(
                f"no enrichment config for study "
                f"{genotype_data.study_id}")
        enrichment_config = self.get_enrichment_config(genotype_data)
        assert enrichment_config is not None
        if background_id is None:
            background_id = enrichment_config["default_background_model"]
        if counter_id is None:
            counter_id = enrichment_config["default_counting_model"]

        background = self.create_background(background_id)
        counter = self.create_counter(counter_id)
        return EnrichmentTool(background, counter)
