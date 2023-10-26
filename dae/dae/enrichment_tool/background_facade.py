import logging

from typing import Optional, Any, cast

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.enrichment_tool.samocha_background import \
    SamochaEnrichmentBackground
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class BackgroundFacade:
    """Facade to create and find enrichment background."""

    def __init__(self, grr: GenomicResourceRepo):
        self._background_cache: dict[str, BaseEnrichmentBackground] \
            = {}
        self._enrichment_config_cache: dict[str, Box] = {}
        self.grr = grr

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

    def get_study_enrichment_config(
        self, study: GenotypeData
    ) -> dict[str, Any]:
        return cast(dict[str, Any], study.config["enrichment"])

    def has_background(self, study: GenotypeData, background_id: str) -> bool:
        config = self.get_study_enrichment_config(study)
        return background_id in config["selected_background_models"]

    def get_study_background(
        self, study: GenotypeData,
        background_id: str
    ) -> Optional[BaseEnrichmentBackground]:
        """Construct and return an enrichment background."""
        config = study.config.get("enrichment")
        if config is None:
            return None
        if not config["enabled"]:
            return None
        if background_id not in config["selected_background_models"]:
            logger.warning(
                "enrichment background <%s> not found in study <%s> "
                "enrichment config", background_id, study.study_id)
            return None
        if background_id in self._background_cache:
            return self._background_cache[background_id]

        background = self._build_background_from_resource(background_id)
        self._background_cache[background_id] = background
        return background

    def get_all_study_backgrounds(
        self, study: GenotypeData
    ) -> list[BaseEnrichmentBackground]:
        """Collect all enrichment backgrounds configured for a study."""
        config = self.get_study_enrichment_config(study)
        if config is None:
            return []
        if not config["enabled"]:
            return []

        result = []
        for background_id in config["selected_background_models"]:
            background = self.get_study_background(study, background_id)
            if background is None:
                continue
            result.append(background)
        return result
