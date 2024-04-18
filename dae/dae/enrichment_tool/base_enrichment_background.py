from __future__ import annotations

import abc
import logging
from collections.abc import Iterable
from typing import Any, cast

from dae.enrichment_tool.event_counters import (
    EnrichmentResult,
    EventCountersResult,
)
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)

logger = logging.getLogger(__name__)


class BaseEnrichmentBackground(
    abc.ABC,
):
    """Provides class for enrichment background models."""

    def __init__(
        self, resource: GenomicResource,
    ):
        self.resource = resource

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get the background name."""

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    @property
    def background_id(self) -> str:
        return self.resource.resource_id

    @property
    def background_type(self) -> str:
        return self.resource.get_type()

    @abc.abstractmethod
    def load(self) -> None:
        """Load the background data."""

    @abc.abstractmethod
    def is_loaded(self) -> bool:
        """Check if the background data is loaded."""

    @abc.abstractmethod
    def calc_enrichment_test(
        self,
        events_counts: EventCountersResult,
        overlapped_counts: EventCountersResult,
        gene_set: Iterable[str],
        **kwargs: Any,
    ) -> EnrichmentResult:
        """Calculate the enrichment test."""


class BaseEnrichmentResourceBackground(
    BaseEnrichmentBackground,
    ResourceConfigValidationMixin,
):
    """Provides class for enrichment resource background models."""

    def __init__(
        self, resource: GenomicResource,
    ):
        super().__init__(resource)

        self.config = self.validate_and_normalize_schema(
            resource.get_config(), resource,
        )

    @property
    def filename(self) -> str:
        return cast(str, self.config["filename"])

    @property
    def name(self) -> str:
        return cast(str, self.config["name"])

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
        }
