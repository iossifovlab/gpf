'''
Created on Nov 9, 2016

@author: lubo
'''
from collections import Counter

import logging
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats.stats import ttest_ind

from dae.pheno_tool.pheno_common import PhenoResult
from dae.pheno.common import MeasureType
from dae.variants.attributes import Role, Sex
from dae.utils.effect_utils import EffectTypesMixin


LOGGER = logging.getLogger(__name__)


class PhenoToolHelper(object):
    """
    Helper class for PhenoTool. Collects variants and person ids from a study.

    Arguments of the constructor are:

    `study` -- an instance of StudyWrapper or DatasetWrapper
    """

    def __init__(self, study):
        assert study
        self.study = study
        self.effect_types_mixin = EffectTypesMixin()

    def _package_effect_type_group(self, group, variants):
        group = group.lower()
        res = {group: Counter()}
        group_effect_types = self.effect_types_mixin.build_effect_types(group)
        for effect_type in group_effect_types:
            if effect_type not in variants:
                continue
            for person_id in variants[effect_type]:
                res[group][person_id] = 1
        return res

    def study_persons(self, family_ids=[], roles=[Role.prb]):
        assert isinstance(family_ids, list)
        assert isinstance(roles, list)
        persons = set()

        if not family_ids:
            family_ids = self.study.families.keys()

        for family_id in family_ids:
            family = self.study.families[family_id]
            for person in family.members_in_order:
                if person.role in roles:
                    persons.add(person.person_id)
        return persons

    def pheno_filter_persons(self, pheno_filters):
        if not pheno_filters:
            return None

        assert isinstance(pheno_filters, list)

        return self.study._transform_pheno_filters_to_people_ids(
            pheno_filters)

    def study_variants(self, data):
        assert 'effectTypes' in data

        queried_effect_types = set(self.effect_types_mixin.
                                   get_effect_types(**data))
        variants_by_effect = {effect: Counter() for effect in
                              queried_effect_types}

        for variant in self.study.query_variants(**data):
            for allele in variant.matched_alleles:
                for person in filter(None, allele.variant_in_members):
                    for effect in allele.effects.types:
                        if effect in queried_effect_types:
                            variants_by_effect[effect][person] = 1

        for effect_type in data['effectTypes']:
            effect_type = effect_type.lower()
            if effect_type not in self.effect_types_mixin.EFFECT_GROUPS:
                continue
            variants_by_effect.update(self._package_effect_type_group(
                                      effect_type, variants_by_effect))

        return variants_by_effect


class PhenoTool(object):
    """
    Tool to estimate dependency between variants and phenotype measrues.

    Arguments of the constructor are:

    `phenotype_data` -- an instance of PhenotypeData

    `measure_id` -- a phenotype measure ID

    `person_ids` -- an optional list of person IDs to filter the phenotype
    database with

    `normalize_by` -- list of continuous measure names. Default value is
    an empty list
    """

    def __init__(self, phenotype_data, measure_id, person_ids=None,
                 normalize_by=[]):

        self.phenotype_data = phenotype_data
        self.measure_id = measure_id

        assert self.phenotype_data.has_measure(measure_id)
        assert self.phenotype_data.get_measure(self.measure_id).measure_type in \
            [MeasureType.continuous, MeasureType.ordinal]

        self.normalize_by = self._init_normalize_measures(normalize_by)

        # TODO currently filtering only for probands, expand with additional
        # options via PeopleGroup
        all_measures = [self.measure_id] + self.normalize_by

        pheno_df = self.phenotype_data.get_persons_values_df(
            all_measures, person_ids=person_ids, roles=[Role.prb])

        self.pheno_df = pheno_df.dropna()

        if not self.pheno_df.empty:
            self.pheno_df = self._normalize_df(
                self.pheno_df, self.measure_id, self.normalize_by
            )

    def _init_normalize_measures(self, normalize_by):
        normalize_by = [self._get_normalize_measure_id(normalize_measure)
                        for normalize_measure in normalize_by]
        normalize_by = list(filter(None, normalize_by))

        assert all([self.phenotype_data.get_measure(m).measure_type
                    == MeasureType.continuous
                    for m in normalize_by])
        return normalize_by

    def _get_normalize_measure_id(self, normalize_measure):
        assert isinstance(normalize_measure, dict)
        assert all(['measure_name' in normalize_measure,
                    'instrument_name' in normalize_measure])

        if not normalize_measure['instrument_name']:
            normalize_measure['instrument_name'] = \
                self.measure_id.split('.')[0]

        normalize_id = '.'.join([normalize_measure['instrument_name'],
                                 normalize_measure['measure_name']])
        if self.phenotype_data.has_measure(normalize_id) and \
           normalize_id != self.measure_id:
            return normalize_id
        else:
            return None

    @staticmethod
    def join_pheno_df_with_variants(pheno_df, variants):
        assert not pheno_df.empty
        assert isinstance(variants, Counter)

        persons_variants = pd.DataFrame(
            data=list(variants.items()),
            columns=['person_id', 'variant_count'])
        persons_variants = persons_variants.set_index('person_id')

        merged_df = pd.merge(pheno_df, persons_variants,
                             how='left', on=['person_id'])
        merged_df = merged_df.fillna(0)
        return merged_df

    @staticmethod
    def _normalize_df(df, measure_id, normalize_by=[]):
        assert not df.empty

        assert measure_id in df
        assert all([measure_id in df for measure_id in normalize_by])

        if not normalize_by:
            dn = pd.Series(
                index=df.index, data=df[measure_id].to_numpy())
            df.loc[:, 'normalized'] = dn
            return df
        else:
            X = sm.add_constant(df[normalize_by].to_numpy())
            y = df[measure_id]
            model = sm.OLS(y, X)
            fitted = model.fit()

            dn = pd.Series(index=df.index, data=fitted.resid)
            df.loc[:, 'normalized'] = dn
            return df

    @staticmethod
    def _calc_base_stats(arr):
        count = len(arr)
        if count == 0:
            mean = 0
            std = 0
        else:
            mean = np.mean(arr, dtype=np.float64)
            std = 1.96 * \
                np.std(arr, dtype=np.float64) / np.sqrt(count)
        return count, mean, std

    @staticmethod
    def _calc_pv(positive, negative):
        if len(positive) < 2 or len(negative) < 2:
            return 'NA'
        tt = ttest_ind(positive, negative)
        pv = tt[1]
        return pv

    @classmethod
    def _calc_stats(cls, data, sex):
        if len(data) == 0:
            result = PhenoResult()
            result.positive_count = 0
            result.positive_mean = 0
            result.positive_deviation = 0

            result.negative_count = 0
            result.negative_mean = 0
            result.negative_deviation = 0
            result.pvalue = 'NA'
            return result

        positive_index = np.logical_and(
            data['variant_count'] != 0, ~np.isnan(data['variant_count']))

        negative_index = data['variant_count'] == 0

        if sex is None:
            sex_index = None
            positive_sex_index = positive_index
            negative_sex_index = negative_index
        else:
            sex_index = data['sex'] == sex
            positive_sex_index = np.logical_and(
                positive_index, sex_index)
            negative_sex_index = np.logical_and(negative_index,
                                                sex_index)

            assert not np.any(np.logical_and(positive_sex_index,
                                             negative_sex_index))

        positive = data[positive_sex_index].normalized.values
        negative = data[negative_sex_index].normalized.values
        p_val = cls._calc_pv(positive, negative)

        result = PhenoResult()
        result._set_positive_stats(*PhenoTool._calc_base_stats(positive))
        result._set_negative_stats(*PhenoTool._calc_base_stats(negative))
        result.pvalue = p_val

        return result

    def calc(self, variants, sex_split=False):
        """
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
        else:
            result = {}
            for sex in [Sex.M, Sex.F]:
                p = self._calc_stats(merged_df, sex)
                result[sex.name] = p
            return result
