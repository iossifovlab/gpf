import logging

from typing import Optional, Any, cast
from collections import defaultdict

from box import Box

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.enrichment_tool.background import BackgroundBase, SamochaBackground, \
    CodingLenBackground
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class BackgroundFacade:
    """Facade to create and find enrichment background."""

    def __init__(self, grr: GenomicResourceRepo):
        self._background_cache: dict[str, dict[str, BackgroundBase]] = \
            defaultdict(dict)
        self._enrichment_config_cache: dict[str, Box] = {}
        self.grr = grr

    def _build_samocha_background_for_study(
        self, study: GenotypeData
    ) -> BackgroundBase:
        config = study.config["enrichment"]
        background = SamochaBackground(config)
        return background

    def _build_coding_len_background(
        self, study: GenotypeData
    ) -> BackgroundBase:
        config = study.config["enrichment"]
        background = CodingLenBackground(config)
        return background

    def _build_background_from_resource(
        self, resource_id: str
    ) -> BackgroundBase:
        resource = self.grr.get_resource(resource_id)
        if resource.get_type() == "gene_weights_enrichment_background":
            return GeneWeightsEnrichmentBackground(resource)

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
        return background_id in config["background"]

    def get_study_background(
        self, study: GenotypeData,
        background_id: str
    ) -> Optional[BackgroundBase]:
        """Construct and return an enrichment background."""
        config = study.config.get("enrichment")
        if config is None:
            return None
        if not config["enabled"]:
            return None
        if background_id not in config["selected_background_values"]:
            logger.warning(
                "enrichment background <%s> not found in study <%s> "
                "enrichment config", background_id, study.study_id)
            return None
        if background_id == "samocha_background_model":
            return self._build_samocha_background_for_study(study)
        if background_id == "coding_len_background_model":
            return self._build_coding_len_background(study)

        return self._build_background_from_resource(background_id)
