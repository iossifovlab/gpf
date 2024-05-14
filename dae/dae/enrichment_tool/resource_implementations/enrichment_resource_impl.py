from __future__ import annotations

import logging
from typing import Any

from dae.enrichment_tool.base_enrichment_background import (
    BaseEnrichmentBackground,
)
from dae.enrichment_tool.gene_weights_background import (
    GeneWeightsEnrichmentBackground,
)
from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class EnrichmentBackgroundResourceImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Provides class for enrichment background resource implementation."""

    def __init__(
        self, resource: GenomicResource, background: BaseEnrichmentBackground,
    ):
        super().__init__(resource)
        self.background = background

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    @property
    def files(self) -> set[str]:
        res = set()
        res.add(self.resource.get_config()["filename"])
        return res

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any,
    ) -> list[Task]:
        return []

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"


def build_gene_weights_enrichment_background(
    resource: GenomicResource,
) -> EnrichmentBackgroundResourceImplementation:
    background = GeneWeightsEnrichmentBackground(resource)
    return EnrichmentBackgroundResourceImplementation(resource, background)


def build_samocha_enrichment_background(
    resource: GenomicResource,
) -> EnrichmentBackgroundResourceImplementation:
    background = SamochaEnrichmentBackground(resource)
    return EnrichmentBackgroundResourceImplementation(resource, background)
