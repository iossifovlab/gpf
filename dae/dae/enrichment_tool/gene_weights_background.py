from __future__ import annotations

import logging
from collections.abc import Iterable
from functools import cached_property
from typing import Any, cast

import pandas as pd
from scipy import stats

from dae.enrichment_tool.base_enrichment_background import (
    BaseEnrichmentBackground,
    BaseEnrichmentResourceBackground,
)
from dae.enrichment_tool.event_counters import (
    EnrichmentResult,
    EnrichmentSingleResult,
    EventCountersResult,
)
from dae.gene_scores.implementations.gene_scores_impl import (
    build_gene_score_from_resource,
)
from dae.genomic_resources.repository import GenomicResource

logger = logging.getLogger(__name__)


class GeneWeightsEnrichmentBackground(BaseEnrichmentResourceBackground):
    """Provides class for gene weights enrichment background model."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "gene_weights_enrichment_background":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        super().__init__(resource)

        self._total: float | None = None
        self._gene_weights: dict[str, float] | None = None

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
        events_prob: float, events_count: int, observed: int,
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
        events_counts: EventCountersResult,
        overlapped_counts: EventCountersResult,
        gene_set: Iterable[str],
        **kwargs: Any,
    ) -> EnrichmentResult:
        """Calculate enrichment statistics."""
        gene_syms = set(gs.upper() for gs in gene_set)

        events_prob = self.genes_prob(gene_syms)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.all, overlapped_counts.all)
        all_result = EnrichmentSingleResult(
            "all", events_counts.all, overlapped_counts.all,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.rec, overlapped_counts.rec)
        rec_result = EnrichmentSingleResult(
            "rec", events_counts.rec, overlapped_counts.rec,
            expected, pvalue, overlapped_counts.rec_genes)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.male, overlapped_counts.male)
        male_result = EnrichmentSingleResult(
            "male", events_counts.male, overlapped_counts.male,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.female,
            overlapped_counts.female)
        female_result = EnrichmentSingleResult(
            "female", events_counts.female, overlapped_counts.female,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.unspecified,
            overlapped_counts.unspecified)
        unspecified_result = EnrichmentSingleResult(
            "unspecified", events_counts.unspecified,
            overlapped_counts.unspecified,
            expected, pvalue)

        return EnrichmentResult(
            all_result,
            rec_result,
            male_result,
            female_result,
            unspecified_result,
        )


class GeneScoreEnrichmentBackground(BaseEnrichmentBackground):
    """Provides class for gene weights enrichment background model."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)

        if resource.get_type() != "gene_score":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        self.resource = resource
        self.gene_score = build_gene_score_from_resource(self.resource)
        if len(self.gene_score.score_definitions) != 1:
            raise ValueError(
                f"gene score is expected to have one score included; "
                f"found {len(self.gene_score.score_definitions)} scores")

        self._total: float | None = None
        self._gene_weights: dict[str, float] | None = None

    @property
    def filename(self) -> str:
        return cast(str, self.gene_score.config["filename"])

    @cached_property
    def score_id(self) -> str:
        score_ids = self.gene_score.get_all_scores()
        assert len(score_ids) == 1
        return score_ids[0]

    @cached_property
    def name(self) -> str:
        return self.gene_score.score_definitions[self.score_id].name

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    @property
    def background_id(self) -> str:
        return self.resource.resource_id

    @property
    def background_type(self) -> str:
        return self.resource.get_type()

    def is_loaded(self) -> bool:
        return self._total is not None and self._gene_weights is not None

    def load(self) -> None:
        """Load enrichment background model."""
        if self.is_loaded():
            logger.info(
                "loading already loaded enrichment background model: %s",
                self.resource.resource_id)
            return

        self._gene_weights = {}
        score_id = self.score_id
        for row in self.gene_score.df.iterrows():
            self._gene_weights[row[1]["gene"]] = \
                float(row[1][score_id])
        self._total = float(self.gene_score.df[score_id].sum())

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
        events_prob: float, events_count: int, observed: int,
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
        events_counts: EventCountersResult,
        overlapped_counts: EventCountersResult,
        gene_set: Iterable[str],
        **kwargs: Any,
    ) -> EnrichmentResult:
        """Calculate enrichment statistics."""
        gene_syms = set(gs.upper() for gs in gene_set)

        events_prob = self.genes_prob(gene_syms)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.all, overlapped_counts.all)
        all_result = EnrichmentSingleResult(
            "all", events_counts.all, overlapped_counts.all,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.rec, overlapped_counts.rec)
        rec_result = EnrichmentSingleResult(
            "rec", events_counts.rec, overlapped_counts.rec,
            expected, pvalue, overlapped_counts.rec_genes)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.male, overlapped_counts.male)
        male_result = EnrichmentSingleResult(
            "male", events_counts.male, overlapped_counts.male,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.female,
            overlapped_counts.female)
        female_result = EnrichmentSingleResult(
            "female", events_counts.female, overlapped_counts.female,
            expected, pvalue)

        expected, pvalue = self.calc_expected_observed_pvalue(
            events_prob, events_counts.unspecified,
            overlapped_counts.unspecified)
        unspecified_result = EnrichmentSingleResult(
            "unspecified", events_counts.unspecified,
            overlapped_counts.unspecified,
            expected, pvalue)

        return EnrichmentResult(
            all_result,
            rec_result,
            male_result,
            female_result,
            unspecified_result,
        )
