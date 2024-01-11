import logging

from collections import Counter
from typing import Union, Any, Optional, cast

import numpy as np
import pandas as pd

from scipy.stats import ttest_ind  # type: ignore

from dae.pheno.utils.lin_regress import LinearRegression

from dae.pheno.common import MeasureType
from dae.variants.attributes import Role, Sex
from dae.variants.family_variant import FamilyAllele
from dae.effect_annotation.effect import EffectTypesMixin, expand_effect_types
from dae.studies.study import GenotypeData
from dae.pheno.pheno_db import PhenotypeData


logger = logging.getLogger(__name__)


class PhenoResult:
    """Represents a result of PhenoTool calculation."""

    def __init__(self) -> None:
        self.pvalue = np.nan
        self.positive_count = np.nan
        self.positive_mean = np.nan
        self.positive_deviation = np.nan
        self.negative_count = np.nan
        self.negative_mean = np.nan
        self.negative_deviation = np.nan

    def set_positive_stats(
        self, p_count: int, p_mean: float, p_std: float
    ) -> None:
        self.positive_count = p_count
        self.positive_mean = p_mean
        self.positive_deviation = p_std

    def set_negative_stats(
        self, n_count: int, n_mean: float, n_std: float
    ) -> None:
        self.negative_count = n_count
        self.negative_mean = n_mean
        self.negative_deviation = n_std

    def __repr__(self) -> str:
        return f"PhenoResult: pvalue={self.pvalue}; "\
            f"pos={self.positive_count} " \
            f"(neg={self.negative_count})"


class PhenoToolHelper:
    """Helper class for PhenoTool.

    Collects variants and person ids from genotype data.

    Arguments of the constructor are:

    `genotype_data` -- an instance of StudyWrapper
    """

    def __init__(
        self, genotype_data: GenotypeData, phenotype_data: PhenotypeData
    ) -> None:
        assert genotype_data
        self.genotype_data = genotype_data
        self.phenotype_data = phenotype_data
        self.effect_types_mixin = EffectTypesMixin()

    def _package_effect_type_group(
        self, group: str, variants: Any
    ) -> dict[str, Counter]:
        res: dict[str, Any] = {group: Counter()}

        group_effect_types = self.effect_types_mixin.build_effect_types(group)

        for effect_type in group_effect_types:
            if effect_type not in variants:
                continue
            for person_id in variants[effect_type]:
                res[group][person_id] = 1
        return res

    def genotype_data_persons(
        self, family_ids: Optional[list[str]] = None,
        roles: Optional[list[Role]] = None
    ) -> set[str]:
        """Collect person ids from genotype data."""
        if family_ids is None:
            family_ids = []
        if roles is None:
            roles = [Role.prb]

        assert isinstance(family_ids, list)
        assert isinstance(roles, list)
        persons = set()

        if not family_ids:
            family_ids = list(self.genotype_data.families.keys())

        for family_id in family_ids:
            family = self.genotype_data.families[family_id]
            for person in family.members_in_order:
                if person.role in roles:
                    persons.add(person.person_id)
        return persons

    def genotype_data_variants(
        self, data: dict, effect_groups: list[str]
    ) -> dict[str, Counter]:
        """Collect effect groups variants."""
        assert "effect_types" in data, data

        effect_types = set(data["effect_types"])
        queried_effect_types = set(expand_effect_types(effect_types))

        variants_by_effect: dict[str, Counter] = {
            effect: Counter() for effect in queried_effect_types
        }

        for variant in self.genotype_data.query_variants(**data):
            for allele in variant.matched_alleles:
                fa = cast(FamilyAllele, allele)
                assert fa.effects is not None

                for person in filter(None, fa.variant_in_members):
                    for effect in fa.effects.types:
                        if effect in queried_effect_types:
                            variants_by_effect[effect][person] = 1

        for effect_type in effect_groups:
            if effect_type not in self.effect_types_mixin.EFFECT_GROUPS:
                continue
            variants_by_effect.update(
                self._package_effect_type_group(
                    effect_type, variants_by_effect
                )
            )
        logger.debug("variants_by_effect: %s", list(variants_by_effect.keys()))

        variants_by_effect = {
            k: variants_by_effect[k]
            for k in effect_groups
            if k in variants_by_effect
        }
        logger.debug("variants_by_effect: %s", list(variants_by_effect.keys()))

        return variants_by_effect


class PhenoTool:
    """Tool to estimate dependency between variants and phenotype measrues.

    Arguments of the constructor are:

    `phenotype_data` -- an instance of PhenotypeData

    `measure_id` -- a phenotype measure ID

    `person_ids` -- an optional list of person IDs to filter the phenotype
    database with

    `normalize_by` -- list of continuous measure names. Default value is
    an empty list
    """

    def __init__(
        self, phenotype_data: PhenotypeData,
        measure_id: str,
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        normalize_by: Optional[list[dict[str, str]]] = None,
    ) -> None:
        if normalize_by is None:
            normalize_by = []

        self.phenotype_data = phenotype_data
        self.measure_id = measure_id

        assert self.phenotype_data.has_measure(measure_id)
        assert self.phenotype_data.get_measure(self.measure_id).measure_type \
            in [MeasureType.continuous, MeasureType.ordinal]

        self.normalize_by = self._init_normalize_measures(normalize_by)

        # TODO currently filtering only for probands, expand with additional
        # options via PeopleGroup
        all_measures = [self.measure_id] + self.normalize_by

        pheno_df = self.phenotype_data.get_persons_values_df(
            all_measures,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=[Role.prb]
        )

        self.pheno_df = pheno_df.dropna()

        if not self.pheno_df.empty:
            self.pheno_df = self._normalize_df(
                self.pheno_df, self.measure_id, self.normalize_by
            )

    def _init_normalize_measures(
        self, normalize_by: list[dict[str, str]]
    ) -> list[str]:
        result = list(filter(
            None,
            [
                self._get_normalize_measure_id(normalize_measure)
                for normalize_measure in normalize_by
            ]))

        assert all(
            self.phenotype_data.get_measure(m).measure_type
            == MeasureType.continuous
            for m in result
        )
        return result

    def _get_normalize_measure_id(
        self, normalize_measure: dict[str, str]
    ) -> Optional[str]:
        assert isinstance(normalize_measure, dict)
        assert "measure_name" in normalize_measure
        assert "instrument_name" in normalize_measure

        if not normalize_measure["instrument_name"]:
            normalize_measure["instrument_name"] = \
                self.measure_id.split(".")[0]

        normalize_id = ".".join(
            [
                normalize_measure["instrument_name"],
                normalize_measure["measure_name"],
            ]
        )
        if self.phenotype_data.has_measure(normalize_id) and \
                normalize_id != self.measure_id:
            return normalize_id

        return None

    @staticmethod
    def join_pheno_df_with_variants(
        pheno_df: pd.DataFrame, variants: Counter
    ) -> pd.DataFrame:
        """Join phenotype dataframe with variants."""
        assert not pheno_df.empty
        assert isinstance(variants, Counter)

        persons_variants = pd.DataFrame(
            data=list(variants.items()), columns=["person_id", "variant_count"]
        )
        persons_variants = persons_variants.set_index("person_id")

        merged_df = pd.merge(
            pheno_df, persons_variants, how="left", on=["person_id"]
        )
        merged_df = merged_df.fillna(0)
        return merged_df

    @staticmethod
    def _normalize_df(
        df: pd.DataFrame, measure_id: str,
        normalize_by: Optional[list[str]] = None
    ) -> pd.DataFrame:
        if normalize_by is None:
            normalize_by = []

        assert not df.empty

        assert measure_id in df
        assert all(measure_id in df for measure_id in normalize_by)

        if not normalize_by:
            dn = pd.Series(index=df.index, data=df[measure_id].to_numpy())
            df.loc[:, "normalized"] = dn
            return df

        x = df[normalize_by].to_numpy()
        y = df[measure_id]
        fitted = LinearRegression().fit(x, y)
        resids = y - fitted.predict(x)

        dn = pd.Series(index=df.index, data=resids)
        df.loc[:, "normalized"] = dn
        return df

    @staticmethod
    def _calc_base_stats(arr: np.ndarray) -> tuple[int, float, float]:
        count = len(arr)
        if count == 0:
            mean = 0.0
            std = 0.0
        else:
            mean = float(np.mean(arr, dtype=np.float64))
            std = float(1.96 * np.std(arr, dtype=np.float64) / np.sqrt(count))
        return count, mean, std

    @staticmethod
    def _calc_pv(
        positive: np.ndarray,
        negative: np.ndarray
    ) -> float:
        if len(positive) < 2 or len(negative) < 2:
            return "NA"  # type: ignore
        tt = ttest_ind(positive, negative)
        pv = tt[1]
        return float(pv)

    @classmethod
    def _calc_stats(
        cls, data: pd.DataFrame, sex: Optional[Sex]
    ) -> PhenoResult:
        if len(data) == 0:
            result = PhenoResult()
            result.positive_count = 0
            result.positive_mean = 0
            result.positive_deviation = 0

            result.negative_count = 0
            result.negative_mean = 0
            result.negative_deviation = 0
            result.pvalue = "NA"  # type: ignore
            return result

        positive_index = np.logical_and(
            data["variant_count"] != 0, ~np.isnan(data["variant_count"])
        )

        negative_index = np.array(data["variant_count"] == 0)

        if sex is None:
            sex_index = None
            positive_sex_index = positive_index
            negative_sex_index = negative_index
        else:
            sex_index = data["sex"] == sex
            positive_sex_index = np.logical_and(positive_index, sex_index)
            negative_sex_index = np.logical_and(negative_index, sex_index)

            assert not np.any(
                np.logical_and(positive_sex_index, negative_sex_index)
            )

        positive = np.array(data[positive_sex_index].normalized.values)
        negative = np.array(data[negative_sex_index].normalized.values)
        p_val = cls._calc_pv(positive, negative)

        result = PhenoResult()
        result.set_positive_stats(*PhenoTool._calc_base_stats(positive))
        result.set_negative_stats(*PhenoTool._calc_base_stats(negative))
        result.pvalue = p_val

        return result

    def calc(
        self, variants: Counter,
        sex_split: bool = False
    ) -> Union[dict[str, PhenoResult], PhenoResult]:
        """Perform calculation.

        `variants` -- an instance of Counter, matching personIds to
        an amount of variants

        `sex_split` -- should we split the result by sex or not. Default
        is `False`.

        """
        if not self.pheno_df.empty:
            merged_df = PhenoTool.join_pheno_df_with_variants(
                self.pheno_df, variants
            )
        else:
            merged_df = self.pheno_df

        if not sex_split:
            return self._calc_stats(merged_df, None)

        result = {}
        for sex in [Sex.M, Sex.F]:
            p = self._calc_stats(merged_df, sex)
            result[sex.name] = p
        return result
