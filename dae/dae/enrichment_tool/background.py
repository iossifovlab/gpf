from __future__ import annotations

import abc

from typing import cast, Iterable, Any

from scipy import stats
import pandas as pd
import numpy as np

from dae.enrichment_tool.event_counters import \
    overlap_enrichment_result_dict, \
    EnrichmentResult, EventsCounterResult
from dae.enrichment_tool.genotype_helper import ChildrenStats


class BackgroundBase(abc.ABC):
    """Base class for Background."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        assert self.name is not None
        self.config = config
        self.load()

    @abc.abstractmethod
    def load(self) -> None:
        """Load the background data."""

    @abc.abstractmethod
    def calc_enrichment_test(
        self,
        events_counts: EventsCounterResult,
        gene_set: Iterable[str],
        **kwargs: Any
    ) -> dict[str, EnrichmentResult]:
        """Calculate the enrichment test."""


class BackgroundCommon(BackgroundBase):
    """A common background base class."""

    @abc.abstractmethod
    def _count(self, gene_syms: set[str]) -> int:
        """Count the expected events in the specified genes."""

    @property
    @abc.abstractmethod
    def _total(self) -> int:
        """Count the total number of expected events."""

    def genes_prob(self, genes: set[str]) -> float:
        return self._prob(genes)

    def _prob(self, gene_syms: set[str]) -> float:
        assert self._total > 0
        return float(self._count(gene_syms)) / self._total

    def _calc_enrichment_results_stats(
        self, background_prob: float, result: EnrichmentResult
    ) -> None:
        assert result.events is not None
        events_count = len(result.events)
        result.expected = background_prob * events_count

        assert result.overlapped is not None
        if not result.overlapped:
            result.pvalue = 1.0
        else:
            assert len(result.overlapped) >= 1.0, result.overlapped
            binom = stats.binomtest(
                len(result.overlapped), events_count, p=background_prob
            )
            result.pvalue = binom.pvalue

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

    # def calc_stats(
    #     self, effect_types: Iterable[str],
    #     events_counts: EventsCounterResult,
    #     gene_set: Iterable[str],
    #     children_by_sex: dict[str, set[str]]
    # ) -> dict[str, EnrichmentResult]:
    #     """Calculate enrichment statistics."""
    #     gene_syms = set(gs.upper() for gs in gene_set)
    #     overlap_counts = overlap_enrichment_result_dict(
    #         events_counts, gene_syms)

    #     background_prob = self._prob(gene_syms)

    #     self._calc_enrichment_results_stats(
    #         background_prob, enrichment_results["all"]
    #     )
    #     self._calc_enrichment_results_stats(
    #         background_prob, enrichment_results["rec"]
    #     )
    #     self._calc_enrichment_results_stats(
    #         background_prob, enrichment_results["male"]
    #     )
    #     self._calc_enrichment_results_stats(
    #         background_prob, enrichment_results["female"]
    #     )

    #     return enrichment_results


# class SynonymousBackground(BackgroundCommon):
#     TRANSMITTED_STUDY_NAME = "w1202s766e611"

#     @staticmethod
#     def _collect_affected_gene_syms(vs):
#         return [
#             set(ge["sym"].upper() for ge in v.requestedGeneEffects)
#             for v in vs
#         ]

#     @staticmethod
#     def _collect_unique_gene_syms(affected_gene_sets):
#         gene_set = set()
#         for gs in affected_gene_sets:
#             gene_set |= set(gs)
#         return gene_set

#     @staticmethod
#     def _count_gene_syms(affected_gene_sets):
#         background = Counter()
#         for gene_set in affected_gene_sets:
#             for gene_sym in gene_set:
#                 background[gene_sym] += 1
#         return background

#     def _build_synonymous_background(self):
#         genotype_data_study = self.variants_db.get(
#             self.TRANSMITTED_STUDY_NAME)
#         vs = genotype_data_study.query_variants(
#             # inheritance=str(Inheritance.transmitted.name),
#             ultraRareOnly=True,
#             minParentsCalled=600,
#             effectTypes=["synonymous"],
#         )
#         affected_gene_syms = SynonymousBackground\
#             ._collect_affected_gene_syms(vs)

#         base = [gs for gs in affected_gene_syms if len(gs) == 1]
#         foreground = [gs for gs in affected_gene_syms if len(gs) > 1]

#         base_counts = SynonymousBackground._count_gene_syms(base)

#         base_sorted = sorted(
#             zip(list(base_counts.keys()), list(base_counts.values()))
#         )

#         background = np.array(
#             base_sorted, dtype=[("sym", "|U32"), ("raw", ">i4")]
#         )

#         return (background, foreground)

#     def _load_and_prepare_build(self):
#         pass

#     def __init__(self, config, variants_db=None):
#         super().__init__(
#             "synonymousBackgroundModel", config
#         )
#         assert variants_db is not None
#         self.variants_db = variants_db

#     def generate_cache(self):
#         self.background, self.foreground = \
#             self._build_synonymous_background()

#     def load(self):
#         self.background, self.foreground = self._load_and_prepare_build()
#         return self.background

#     def _count_foreground_events(self, gene_syms):
#         count = 0
#         for gs in self.foreground:
#             touch = False
#             for sym in gs:
#                 if sym in gene_syms:
#                     touch = True
#                     break
#             if touch:
#                 count += 1
#         return count

#     def _count(self, gene_syms):
#         vpred = np.vectorize(lambda sym: sym in gene_syms)
#         index = vpred(self.background["sym"])
#         base = np.sum(self.background["raw"][index])
#         foreground = self._count_foreground_events(gene_syms)
#         res = base + foreground
#         return res

#     @property
#     def _total(self):
#         return np.sum(self.background["raw"]) + len(self.foreground)


class CodingLenBackground(BackgroundCommon):
    """Defines conding len enrichment background."""

    @property
    def filename(self) -> str:
        return str(self.config["background"][self.name]["file"])

    def _load_and_prepare_build(self) -> pd.DataFrame:
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(
            filename, usecols=["gene_upper", "codingLenInTarget"])

        df = df.rename(
            columns={"gene_upper": "sym", "codingLenInTarget": "raw"}
        )
        df = df.astype(dtype={"sym": np.str_, "raw": np.int32})

        return df

    def __init__(self, config: dict[str, Any]):
        super().__init__(
            "coding_len_background_model", config
        )

    def load(self) -> None:
        self.background = self._load_and_prepare_build()

    def _count(self, gene_syms: set[str]) -> int:
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background["sym"])

        res = np.sum(self.background["raw"][index])
        return cast(int, res)

    @property
    def _total(self) -> int:
        return cast(int, np.sum(self.background["raw"]))


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


class SamochaBackground(BackgroundBase):
    """Represents Samocha's enrichment background model."""

    def __init__(
        self, config: dict[str, Any],
    ):
        self.filename = \
            config["background"]["samocha_background_model"]["file"]

        super().__init__(
            "Samocha's enrichment background model",
            config
        )
        self.background: pd.DataFrame
        self.background_id = "samocha_background_model"
        self.description = ""

        # self.load()

    def _load_and_prepare_build(self) -> pd.DataFrame:
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(
            filename,
            usecols=["gene", "F", "M", "P_LGDS", "P_MISSENSE", "P_SYNONYMOUS"],
        )

        return df

    def load(self) -> None:
        self.background = self._load_and_prepare_build()

    def calc_enrichment_test(
        self,
        events_counts: EventsCounterResult,
        gene_set: Iterable[str],
        **kwargs: Any
    ) -> dict[str, EnrichmentResult]:
        """Calculate enrichment statistics."""
        # pylint: disable=too-many-locals
        effect_types = list(kwargs["event_types"])
        assert len(effect_types) == 1
        effect_type = effect_types[0]

        children_stats = cast(ChildrenStats, kwargs["children_stats"])

        overlapped_counts = overlap_enrichment_result_dict(
            events_counts, gene_set)

        eff = f"P_{effect_type.upper()}"
        assert eff in self.background.columns, (eff, self.background.columns)

        # all_result = enrichment_results["all"]
        # male_result = enrichment_results["male"]
        # female_result = enrichment_results["female"]
        # rec_result = enrichment_results["rec"]

        gene_syms = [g.upper() for g in gene_set]
        df = self.background[self.background["gene"].isin(gene_syms)]

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
