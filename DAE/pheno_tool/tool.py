'''
Created on Nov 9, 2016

@author: lubo
'''
from __future__ import unicode_literals

from builtins import object
from collections import Counter

from scipy.stats.stats import ttest_ind

import numpy as np
import pandas as pd

from pheno_tool.pheno_common import PhenoFilterBuilder, PhenoResult
import statsmodels.api as sm

from pheno.common import MeasureType

from variants.attributes import Role, Sex
import logging

LOGGER = logging.getLogger(__name__)


class PhenoTool(object):
    """
    Tool to estimate dependency between variants and phenotype measrues.

    Arguments of the constructor are:
    `pheno_db` -- a phenotype database

    `measure_id` -- a phenotype measure ID

    `normalize_by` -- list of continuous measure names. Default value is
    an empty list

    `pheno_filters` -- dictionary of measure IDs and filter specifiers. Default
    is empty dictionary.
    """

    def __init__(self, pheno_db, measure_id, normalize_by=[],
                 pheno_filters={}):

        assert pheno_db.has_measure(measure_id)

        self.pheno_db = pheno_db
        self.measure_id = measure_id

        self.normalize_by = [normalize_id for normalize_id in [
            self.get_normalize_measure_id(normalize_name)
            for normalize_name in normalize_by]
            if normalize_id is not None]

        self.normalize_by = [self.get_normalize_measure_id(normalize_name)
                             for normalize_name in normalize_by]
        self.normalize_by = [normalize_id
                             for normalize_id in self.normalize_by
                             if normalize_id is not None]
        print(self.normalize_by)

        assert all([pheno_db.get_measure(m).measure_type
                    == MeasureType.continuous
                    for m in self.normalize_by])
        assert pheno_db.get_measure(measure_id).measure_type in \
            [MeasureType.continuous, MeasureType.ordinal]

        if pheno_filters:
            filter_builder = PhenoFilterBuilder(self.pheno_db)
            self.pheno_filters = [
                filter_builder.make_filter(m, c)
                for m, c in list(pheno_filters.items())
            ]
        else:
            self.pheno_filters = []

        # TODO currently filtering only for probands, expand with additional
        # options via PeopleGroup
        self.pheno_df = self.pheno_db.get_persons_values_df([self.measure_id],
                                                            roles=[Role.prb])
        for f in self.pheno_filters:
            self.pheno_df = f.apply(self.pheno_df)
        self._normalize_df(self.pheno_df, self.measure_id, self.normalize_by)

    def get_normalize_measure_id(self, normalize_name):
        instrument_name = self.measure_id.split('.')[0]
        normalize_id = '.'.join([instrument_name, normalize_name])
        if self.pheno_db.has_measure(normalize_id):
            return normalize_id
        else:
            return None

    @staticmethod
    def _normalize_df(df, measure_id, normalize_by=[]):
        if not normalize_by:
            dn = pd.Series(
                index=df.index, data=df[measure_id].values)
            df['normalized'] = dn
            return df
        else:
            X = sm.add_constant(df[normalize_by])
            y = df[measure_id]
            model = sm.OLS(y, X)
            fitted = model.fit()

            dn = pd.Series(index=df.index, data=fitted.resid)
            df['normalized'] = dn
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
            result = PhenoResult(None, None)
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

        result = PhenoResult(data, sex_index)
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
        assert(isinstance(variants, Counter))
        persons_variants = pd.DataFrame(
            data=list(variants.items()),
            columns=['person_id', 'variant_count'])
        persons_variants.set_index('person_id', inplace=True)

        merged_df = pd.merge(self.pheno_df, persons_variants,
                             how='left', on=['person_id'])
        merged_df.fillna(0, inplace=True)

        if not sex_split:
            return self._calc_stats(merged_df, None)
        else:
            result = {}
            for sex in [Sex.M, Sex.F]:
                p = self._calc_stats(merged_df, sex)
                result[sex.name] = p
            return result
