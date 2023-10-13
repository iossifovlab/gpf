from __future__ import annotations

import logging
from typing import Optional, Any, Iterable

import pandas as pd
from scipy import stats

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin
from dae.task_graph.graph import Task, TaskGraph
from dae.enrichment_tool.event_counters import EventsCounterResult, \
    EnrichmentResult, overlap_enrichment_result_dict
from dae.enrichment_tool.background import BackgroundBase


logger = logging.getLogger(__name__)


class GeneWeightsEnrichmentBackground(
    ResourceConfigValidationMixin,
    GenomicResourceImplementation,
    InfoImplementationMixin,
    BackgroundBase
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        if resource.get_type() != "gene_weights_enrichment_background":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        self.config = self.validate_and_normalize_schema(
            self.config, resource
        )
        BackgroundBase.__init__(
            self, f"GeneWeightsEnrichmentBackground({resource.resource_id})",
            self.config)

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

    def load(self) -> None:
        """Load gene models."""
        if self.is_loaded():
            logger.info(
                "loading already loaded gene models: %s",
                self.resource.resource_id)
            return

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

    def genes_weight(self, genes: Iterable[str]) -> float:
        assert self._gene_weights is not None
        result = 0.0
        for gene in genes:
            result += self._gene_weights.get(gene.upper(), 0.0)
        return result

    def genes_prob(self, genes: Iterable[str]) -> float:
        assert self._total is not None
        return self.genes_weight(genes) / self._total

    @staticmethod
    def calc_expected_observed_pvalue(
        events_prob: float, events_count: int, observed: int
    ) -> tuple[float, float]:
        """Calculate expected event count and binomtest p-value."""
        expected = events_count * events_prob
        if observed == 0:
            return expected, 1.0
        assert observed >= 1
        binom = stats.binomtest(observed, events_count, events_prob)
        return expected, binom.pvalue

    def calc_enrichment_test(
        self,
        events_counts: EventsCounterResult,
        gene_set: Iterable[str],
        **kwargs: Any
    ) -> dict[str, EnrichmentResult]:
        """Calculate enrichment statistics."""
        gene_syms = set(gs.upper() for gs in gene_set)
        overlapped_counts = overlap_enrichment_result_dict(
            events_counts, gene_syms)

        events_prob = self.genes_prob(gene_syms)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, len(events_counts.all), len(overlapped_counts.all))
        all_result = EnrichmentResult(
            "all", events_counts.all, overlapped_counts.all,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, len(events_counts.rec), len(overlapped_counts.rec))
        rec_result = EnrichmentResult(
            "rec", events_counts.rec, overlapped_counts.rec,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, len(events_counts.male), len(overlapped_counts.male))
        male_result = EnrichmentResult(
            "male", events_counts.male, overlapped_counts.male,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, len(events_counts.female),
            len(overlapped_counts.female))
        female_result = EnrichmentResult(
            "female", events_counts.female, overlapped_counts.female,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, len(events_counts.unspecified),
            len(overlapped_counts.unspecified))
        unspecified_result = EnrichmentResult(
            "unspecified", events_counts.unspecified,
            overlapped_counts.unspecified,
            expected, pvalue)

        return {
            "all": all_result,
            "rec": rec_result,
            "male": male_result,
            "female": female_result,
            "unspecified": unspecified_result
        }
