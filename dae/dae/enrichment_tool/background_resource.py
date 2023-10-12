from __future__ import annotations

import logging
from typing import Optional, Any

import pandas as pd

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class EnrichmentBackground(
    ResourceConfigValidationMixin,
    GenomicResourceImplementation,
    InfoImplementationMixin
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        if resource.get_type() != "enrichment_background":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        self.config = self.validate_and_normalize_schema(
            self.config, resource
        )
        self._total: Optional[float] = None
        self._gene_weights: Optional[dict[str, float]] = None

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    @property
    def files(self) -> set[str]:
        res = set()
        res.add(self.resource.get_config()["filename"])
        return res

    def is_loaded(self) -> bool:
        return self._total is not None and self._gene_weights is not None

    def load(self) -> EnrichmentBackground:
        """Load gene models."""
        if self.is_loaded():
            logger.info(
                "loading already loaded gene models: %s",
                self.resource.resource_id)
            return self

        filename = self.resource.get_config()["filename"]
        compression = False
        if filename.endswith(".gz"):
            compression = True
        with self.resource.open_raw_file(
                filename, mode="rt", compression=compression) as infile:

            df = pd.read_csv(infile, sep="\t")
            self._gene_weights = {}
            for row in df.iterrows():

                self._gene_weights[row[1]["gene"]] = \
                    float(row[1]["gene_weight"])
            self._total = float(df.gene_weight.sum())

        return self

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
        }

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any
    ) -> list[Task]:
        return []

    def get_info(self) -> str:
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"
