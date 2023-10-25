from __future__ import annotations
import logging
from typing import Optional, Any, Iterable

import pandas as pd
from scipy import stats

from dae.genomic_resources.repository import GenomicResource
from dae.enrichment_tool.event_counters import EventsCounterResult, \
    EnrichmentResult, overlap_enrichment_result_dict
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground

logger = logging.getLogger(__name__)


class GeneWeightsEnrichmentBackground(BaseEnrichmentBackground):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "gene_weights_enrichment_background":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        super().__init__(
            resource,
            f"gene_weights_enrichment_background({resource.resource_id})"
        )

        self._total: Optional[float] = None
        self._gene_weights: Optional[dict[str, float]] = None

    def is_loaded(self) -> bool:
        return self._total is not None and self._gene_weights is not None

    def load(self) -> None:
        """Load enrichment background model."""
        if self.is_loaded():
            logger.info(
                "loading already loaded enrichment background model: %s",
                self.resource.resource_id)
            return

        filename = self.config["filename"]
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
