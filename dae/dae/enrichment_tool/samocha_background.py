from __future__ import annotations
import logging
from typing import Optional, Any, Iterable, cast

import pandas as pd
from scipy import stats

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import \
    get_base_resource_schema
from dae.enrichment_tool.event_counters import EventsCounterResult, \
    EnrichmentResult, overlap_enrichment_result_dict
from dae.enrichment_tool.genotype_helper import ChildrenStats
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground

logger = logging.getLogger(__name__)


def poisson_test(observed: float, expected: float) -> float:
    """Perform Poisson test.

    Bernard Rosner, Fundamentals of Biostatistics, 8th edition, pp 260-261
    """
    # pylint: disable=invalid-name
    rv = stats.poisson(expected)
    if observed >= expected:
        p = rv.cdf(observed - 1)
        p_value = 2 * (1 - p)
    else:
        p = rv.cdf(observed)
        p_value = 2 * p

    return cast(float, min(p_value, 1.0))


class SamochaEnrichmentBackground(BaseEnrichmentBackground):
    """Represents Samocha's enrichment background model."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "samocha_enrichment_background":
            raise ValueError(
                f"unexpected enrichment background resource type: "
                f"<{resource.get_type()}> for resource "
                f"<{resource.resource_id}>")
        super().__init__(resource)

        self._df: Optional[pd.DataFrame] = None

    @property
    def name(self) -> str:
        return "Samocha's enrichment background model"

    def is_loaded(self) -> bool:
        return self._df is not None

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

            self._df = pd.read_csv(
                infile,
                usecols=[
                    "gene", "F", "M", "P_LGDS", "P_MISSENSE", "P_SYNONYMOUS"
                ]
            )

    def calc_enrichment_test(
        self,
        events_counts: EventsCounterResult,
        gene_set: Iterable[str],
        **kwargs: Any
    ) -> dict[str, EnrichmentResult]:
        """Calculate enrichment statistics."""
        # pylint: disable=too-many-locals
        effect_types = list(kwargs["effect_types"])
        assert len(effect_types) == 1
        effect_type = effect_types[0]

        children_stats = cast(ChildrenStats, kwargs["children_stats"])

        overlapped_counts = overlap_enrichment_result_dict(
            events_counts, gene_set)

        eff = f"P_{effect_type.upper()}"
        assert self._df is not None

        assert eff in self._df.columns, (eff, self._df.columns)

        gene_syms = [g.upper() for g in gene_set]
        df = self._df[self._df["gene"].isin(gene_syms)]

        p_boys = (df["M"] * df[eff]).sum()
        male_expected = p_boys * children_stats.male

        p_girls = (df["F"] * df[eff]).sum()
        female_expected = p_boys * children_stats.female

        expected = p_boys * (
            children_stats.male + children_stats.unspecified) + female_expected
        all_result = EnrichmentResult(
            "all",
            events_counts.all,
            overlapped_counts.all,
            expected,
            poisson_test(
                len(overlapped_counts.all), expected)
        )

        male_result = EnrichmentResult(
            "male",
            events_counts.male,
            overlapped_counts.male,
            male_expected,
            poisson_test(
                len(overlapped_counts.male), male_expected)
        )

        female_result = EnrichmentResult(
            "female",
            events_counts.female,
            overlapped_counts.female,
            female_expected,
            poisson_test(
                len(overlapped_counts.female), female_expected)
        )

        if len(events_counts.rec) == 0 or len(events_counts.all) == 0:
            expected = 0
        else:
            children_count = (
                children_stats.male + children_stats.unspecified
                + children_stats.female
            )
            probability = (
                (children_stats.male + children_stats.unspecified) * p_boys
                + children_stats.female * p_girls) / children_count
            expected = (
                children_count
                * probability
                * len(events_counts.rec)
                / len(events_counts.all)
            )

        pvalue = poisson_test(len(overlapped_counts.rec), expected)
        rec_result = EnrichmentResult(
            "rec",
            events_counts.rec,
            overlapped_counts.rec,
            expected,
            pvalue
        )

        return {
            "all": all_result,
            "rec": rec_result,
            "male": male_result,
            "female": female_result,
            "unspecified": EnrichmentResult(
                "unspecified", [], [], 0.0, 1.0
            )
        }

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string", "required": True},
        }
