from collections import Counter
from scipy import stats  # type: ignore
import numpy as np
import pandas as pd

from dae.enrichment_tool.event_counters import overlap_enrichment_result_dict

# from dae.variants.attributes import Inheritance


class BackgroundBase:
    # @staticmethod
    # def backgrounds():
    #     return {
    #         # 'synonymousBackgroundModel': SynonymousBackground,
    #         "coding_len_background_model": CodingLenBackground,
    #         "samocha_background_model": SamochaBackground,
    #     }

    @staticmethod
    def build_background(background_kind, enrichment_config):
        if background_kind == "coding_len_background_model":
            return CodingLenBackground(enrichment_config)
        elif background_kind == "samocha_background_model":
            return SamochaBackground(enrichment_config)

    def __init__(self, name, config):
        self.background = None
        self.name = name
        assert self.name is not None
        self.config = config
        self.load()

    @property
    def is_ready(self):
        return self.background is not None


class BackgroundCommon(BackgroundBase):
    def __init__(self, name, config):
        super(BackgroundCommon, self).__init__(name, config)

    def _prob(self, gene_syms):
        return 1.0 * self._count(gene_syms) / self._total

    def _calc_enrichment_results_stats(self, background_prob, result):
        events_count = len(result.events)
        result.expected = background_prob * events_count
        result.pvalue = stats.binom_test(
            len(result.overlapped), events_count, p=background_prob
        )

    def calc_stats(
        self, effect_type, enrichment_events, gene_set, children_by_sex
    ):

        gene_syms = [gs.upper() for gs in gene_set]
        overlap_enrichment_result_dict(enrichment_events, gene_syms)

        background_prob = self._prob(gene_syms)

        self._calc_enrichment_results_stats(
            background_prob, enrichment_events["all"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_events["rec"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_events["male"]
        )
        self._calc_enrichment_results_stats(
            background_prob, enrichment_events["female"]
        )

        return enrichment_events


class SynonymousBackground(BackgroundCommon):
    TRANSMITTED_STUDY_NAME = "w1202s766e611"

    @staticmethod
    def _collect_affected_gene_syms(vs):
        return [
            set([ge["sym"].upper() for ge in v.requestedGeneEffects])
            for v in vs
        ]

    @staticmethod
    def _collect_unique_gene_syms(affected_gene_sets):
        gene_set = set()
        for gs in affected_gene_sets:
            gene_set |= set(gs)
        return gene_set

    @staticmethod
    def _count_gene_syms(affected_gene_sets):
        background = Counter()
        for gene_set in affected_gene_sets:
            for gene_sym in gene_set:
                background[gene_sym] += 1
        return background

    def _build_synonymous_background(self):
        genotype_data_study = self.variants_db.get(self.TRANSMITTED_STUDY_NAME)
        vs = genotype_data_study.query_variants(
            # inheritance=str(Inheritance.transmitted.name),
            ultraRareOnly=True,
            minParentsCalled=600,
            effectTypes=["synonymous"],
        )
        affected_gene_syms = SynonymousBackground._collect_affected_gene_syms(
            vs
        )

        base = [gs for gs in affected_gene_syms if len(gs) == 1]
        foreground = [gs for gs in affected_gene_syms if len(gs) > 1]

        base_counts = SynonymousBackground._count_gene_syms(base)

        base_sorted = sorted(
            zip(list(base_counts.keys()), list(base_counts.values()))
        )

        background = np.array(
            base_sorted, dtype=[("sym", "|U32"), ("raw", ">i4")]
        )

        return (background, foreground)

    def _load_and_prepare_build(self):
        pass

    def __init__(self, config, variants_db=None):
        super(SynonymousBackground, self).__init__(
            "synonymousBackgroundModel", config
        )
        assert variants_db is not None
        self.variants_db = variants_db

    def generate_cache(self):
        self.background, self.foreground = self._build_synonymous_background()

    def load(self):
        self.background, self.foreground = self._load_and_prepare_build()
        return self.background

    def _count_foreground_events(self, gene_syms):
        count = 0
        for gs in self.foreground:
            touch = False
            for sym in gs:
                if sym in gene_syms:
                    touch = True
                    break
            if touch:
                count += 1
        return count

    def _count(self, gene_syms):
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background["sym"])
        base = np.sum(self.background["raw"][index])
        foreground = self._count_foreground_events(gene_syms)
        res = base + foreground
        return res

    @property
    def _total(self):
        return np.sum(self.background["raw"]) + len(self.foreground)


class CodingLenBackground(BackgroundCommon):
    @property
    def filename(self):
        return getattr(self.config.background, self.name).file

    def _load_and_prepare_build(self):
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(filename, usecols=["gene_upper", "codingLenInTarget"])

        df = df.rename(
            columns={"gene_upper": "sym", "codingLenInTarget": "raw"}
        )
        df = df.astype(dtype={"sym": np.str_, "raw": np.int32})

        return df

    def __init__(self, config):
        super(CodingLenBackground, self).__init__(
            "coding_len_background_model", config
        )

    def load(self):
        self.background = self._load_and_prepare_build()
        return self.background

    def _count(self, gene_syms):
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background["sym"])

        res = np.sum(self.background["raw"][index])
        return res

    @property
    def _total(self):
        return np.sum(self.background["raw"])


def poisson_test(observed, expected):
    # Bernard Rosner, Fundamentals of Biostatistics, 8th edition,
    # pp 260-261
    rv = stats.poisson(expected)
    if observed >= expected:
        p = rv.cdf(observed - 1)
        p_value = 2 * (1 - p)
    else:
        p = rv.cdf(observed)
        p_value = 2 * p

    return min(p_value, 1)


class SamochaBackground(BackgroundBase):
    @property
    def filename(self):
        return getattr(self.config.background, self.name).file

    def _load_and_prepare_build(self):
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(
            filename,
            usecols=["gene", "F", "M", "P_LGDS", "P_MISSENSE", "P_SYNONYMOUS"],
        )

        return df

    def __init__(self, config):
        super(SamochaBackground, self).__init__(
            "samocha_background_model", config
        )

    def load(self):
        self.background = self._load_and_prepare_build()
        return self.background

    def calc_stats(
        self, effect_type, enrichment_results, gene_set, children_by_sex
    ):

        children_stats = Counter()
        for sex, persons in children_by_sex.items():
            children_stats[sex] = len(persons)

        overlap_enrichment_result_dict(enrichment_results, gene_set)

        eff = "P_{}".format(effect_type.upper())
        assert eff in self.background.columns

        all_result = enrichment_results["all"]
        male_result = enrichment_results["male"]
        female_result = enrichment_results["female"]
        rec_result = enrichment_results["rec"]

        gs = [g.upper() for g in gene_set]
        df = self.background[self.background["gene"].isin(gs)]
        p_boys = (df["M"] * df[eff]).sum()
        # result.male_expected = p_boys * events.male_count
        male_result.expected = p_boys * children_stats["M"]

        p_girls = (df["F"] * df[eff]).sum()
        # result.female_expected = p_girls * events.female_count
        female_result.expected = p_boys * children_stats["F"]

        all_result.expected = male_result.expected + female_result.expected

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
        # p = (p_boys + p_girls) / 2.0
        p = (
            1.0
            * (
                (children_stats["M"] + children_stats["U"]) * p_boys
                + children_stats["F"] * p_girls
            )
            / (children_count)
        )
        #         result.rec_expected = \
        #             (children_stats['M'] + children_stats['F']) * p * p
        if len(rec_result.events) == 0 or len(all_result.events) == 0:
            rec_result.expected = 0
        else:
            rec_result.expected = (
                children_count
                * p
                * len(rec_result.events)
                / len(all_result.events)
            )

        rec_result.pvalue = poisson_test(
            len(rec_result.overlapped), rec_result.expected
        )

        return enrichment_results
