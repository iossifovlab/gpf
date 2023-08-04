from __future__ import annotations

from collections import Counter
import abc
from typing import cast, Iterable

from scipy import stats
import numpy as np
import pandas as pd
from box import Box

from dae.enrichment_tool.event_counters import \
    overlap_enrichment_result_dict, \
    EnrichmentResult


class BackgroundBase(abc.ABC):
    """Base class for Background."""

    @staticmethod
    def build_background(
        background_kind: str, enrichment_config: Box
    ) -> BackgroundBase:
        """Construct a specified type of background."""
        if background_kind == "coding_len_background_model":
            return CodingLenBackground(enrichment_config)
        if background_kind == "samocha_background_model":
            return SamochaBackground(enrichment_config)
        raise ValueError(f"unexpected background: {background_kind}")

    def __init__(self, name: str, config: Box):
        self.background: pd.DataFrame
        self.name = name
        assert self.name is not None
        self.config = config
        self.load()

    @property
    def is_ready(self) -> bool:
        return self.background is not None

    @abc.abstractmethod
    def load(self) -> None:
        """Load the background data."""

    @abc.abstractmethod
    def calc_stats(
        self, effect_types: Iterable[str],
        enrichment_results: dict[str, EnrichmentResult],
        gene_set: Iterable[str],
        children_by_sex: dict[str, set[str]]
    ) -> dict[str, EnrichmentResult]:
        """Calculate the enrichment statistics."""


class BackgroundCommon(BackgroundBase):
    """A common background base class."""

    @abc.abstractmethod
    def _count(self, gene_syms: set[str]) -> int:
        """Count the expected events in the specified genes."""

    @property
    @abc.abstractmethod
    def _total(self) -> int:
        """Count the total number of expected events."""

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
        result.pvalue = stats.binom_test(
            len(result.overlapped), events_count, p=background_prob
        )

    def calc_stats(
        self, effect_types: Iterable[str],
        enrichment_results: dict[str, EnrichmentResult],
        gene_set: Iterable[str],
        children_by_sex: dict[str, set[str]]
    ) -> dict[str, EnrichmentResult]:
        """Calculate enrichment statistics."""
        gene_syms = set(gs.upper() for gs in gene_set)
        overlap_enrichment_result_dict(enrichment_results, gene_syms)

        background_prob = self._prob(gene_syms)

        self._calc_enrichment_results_stats(
            background_prob, enrichment_results["all"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results["rec"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results["male"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results["female"]
        )

        return enrichment_results


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
        return str(getattr(self.config.background, self.name).file)

    def _load_and_prepare_build(self) -> pd.DataFrame:
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(filename, usecols=["gene_upper", "codingLenInTarget"])

        df = df.rename(
            columns={"gene_upper": "sym", "codingLenInTarget": "raw"}
        )
        df = df.astype(dtype={"sym": np.str_, "raw": np.int32})

        return df

    def __init__(self, config: Box):
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

    @property
    def filename(self) -> str:
        return cast(str, getattr(self.config.background, self.name).file)

    def _load_and_prepare_build(self) -> pd.DataFrame:
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(
            filename,
            usecols=["gene", "F", "M", "P_LGDS", "P_MISSENSE", "P_SYNONYMOUS"],
        )

        return df

    def __init__(self, config: Box):
        super().__init__(
            "samocha_background_model", config
        )

    def load(self) -> None:
        self.background = self._load_and_prepare_build()

    def calc_stats(
        self, effect_types: Iterable[str],
        enrichment_results: dict[str, EnrichmentResult],
        gene_set: Iterable[str],
        children_by_sex: dict[str, set[str]]
    ) -> dict[str, EnrichmentResult]:
        """Calculate enrichment statistics."""
        # pylint: disable=too-many-locals
        children_stats: dict[str, int] = Counter()
        for sex, persons in children_by_sex.items():
            children_stats[sex] = len(persons)

        overlap_enrichment_result_dict(enrichment_results, gene_set)

        ets = list(effect_types)
        assert len(ets) == 1
        effect_type = ets[0]

        eff = f"P_{effect_type.upper()}"
        assert eff in self.background.columns, (eff, self.background.columns)

        all_result = enrichment_results["all"]
        male_result = enrichment_results["male"]
        female_result = enrichment_results["female"]
        rec_result = enrichment_results["rec"]

        gene_syms = [g.upper() for g in gene_set]
        df = self.background[self.background["gene"].isin(gene_syms)]
        p_boys = (df["M"] * df[eff]).sum()
        male_result.expected = p_boys * children_stats["M"]

        p_girls = (df["F"] * df[eff]).sum()
        female_result.expected = p_boys * children_stats["F"]

        assert male_result.expected is not None
        assert female_result.expected is not None

        all_result.expected = \
            p_boys * (children_stats["M"] + children_stats["U"]) + \
            female_result.expected

        assert all_result.expected is not None
        assert all_result.overlapped is not None
        assert male_result.overlapped is not None
        assert female_result.overlapped is not None
        all_result.pvalue = poisson_test(
            len(all_result.overlapped), all_result.expected
        )
        male_result.pvalue = poisson_test(
            len(male_result.overlapped), male_result.expected
        )
        female_result.pvalue = poisson_test(
            len(female_result.overlapped), female_result.expected
        )

        children_count = (
            children_stats["M"] + children_stats["U"] + children_stats["F"]
        )
        probability = ((children_stats["M"] + children_stats["U"]) * p_boys
                       + children_stats["F"] * p_girls) / children_count

        assert rec_result.events is not None
        assert all_result.events is not None
        if len(rec_result.events) == 0 or len(all_result.events) == 0:
            rec_result.expected = 0
        else:
            rec_result.expected = (
                children_count
                * probability
                * len(rec_result.events)
                / len(all_result.events)
            )
        assert rec_result.overlapped is not None
        assert rec_result.expected is not None
        rec_result.pvalue = poisson_test(
            len(rec_result.overlapped), rec_result.expected
        )

        return enrichment_results
