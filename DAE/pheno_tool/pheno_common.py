'''
Created on Nov 29, 2016

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from collections import Counter

import numpy as np
from pheno.common import MeasureType


class PhenoFilter(object):

    def __init__(self, phdb, measure_id):
        assert phdb.has_measure(measure_id)

        self.phdb = phdb
        self.measure_id = measure_id


class PhenoFilterSet(PhenoFilter):

    def __init__(self, phdb, measure_id, values_set):
        super(PhenoFilterSet, self).__init__(phdb, measure_id)

        measure_type = phdb.get_measure(measure_id).measure_type
        assert measure_type == MeasureType.categorical

        assert isinstance(values_set, list) or isinstance(values_set, set)
        self.value_set = values_set

    def apply(self, df):
        return df[df[self.measure_id].isin(self.value_set)]


class PhenoFilterRange(PhenoFilter):

    def __init__(self, phdb, measure_id, values_range):
        super(PhenoFilterRange, self).__init__(phdb, measure_id)
        measure_type = phdb.get_measure(measure_id).measure_type
        assert measure_type == MeasureType.continuous or \
            measure_type == MeasureType.ordinal

        assert isinstance(values_range, list) or \
            isinstance(values_range, tuple)
        self.values_min, self.values_max = values_range

    def apply(self, df):
        if self.values_min is not None and self.values_max is not None:
            return df[np.logical_and(
                df[self.measure_id] >= self.values_min,
                df[self.measure_id] <= self.values_max
            )]
        elif self.values_min is not None:
            return df[df[self.measure_id] >= self.values_min]
        elif self.values_max is not None:
            return df[df[self.measure_id] <= self.values_max]
        else:
            return df[-np.isnan(df[self.measure_id])]


class PhenoFilterBuilder(object):

    def __init__(self, phdb):
        self.phdb = phdb

    def make_filter(self, measure_id, constraints):
        measure = self.phdb.get_measure(measure_id)
        assert measure is not None
        if measure.measure_type == MeasureType.categorical:
            return PhenoFilterSet(self.phdb, measure_id, constraints)
        else:
            return PhenoFilterRange(self.phdb, measure_id, constraints)


class PhenoResult(object):

    def __init__(self, df, index=None):
        self.df = df
        self.genotypes_df = self._select_genotype(df, index)
        self.phenotypes_df = self._select_phenotype(df, index)
        self.pvalue = np.nan
        self.positive_count = np.nan
        self.positive_mean = np.nan
        self.positive_deviation = np.nan
        self.negative_count = np.nan
        self.negative_mean = np.nan
        self.negative_deviation = np.nan

    @staticmethod
    def _select_genotype(df, index):
        if df is None:
            return None
        gdf = df[['person_id', 'sex', 'role', 'variant_count']]
        if index is not None:
            gdf = gdf[index]
        return gdf

    @staticmethod
    def _select_phenotype(df, index):
        if df is None:
            return None

        columns = list(df.columns)
        del columns[columns.index('variant_count')]
        del columns[columns.index('family_id')]

        pdf = df[columns]
        if index is not None:
            pdf = pdf[index]
        return pdf

    def _set_positive_stats(self, p_count, p_mean, p_std):
        self.positive_count = p_count
        self.positive_mean = p_mean
        self.positive_deviation = p_std

    def _set_negative_stats(self, n_count, n_mean, n_std):
        self.negative_count = n_count
        self.negative_mean = n_mean
        self.negative_deviation = n_std

    @property
    def genotypes(self):
        result = Counter()
        if self.genotypes_df is None:
            return result

        for _index, row in self.genotypes_df.iterrows():
            result[row['person_id']] = row['variant_count']
        return result

    @property
    def phenotypes(self):
        result = {}
        if self.phenotypes_df is None:
            return None
        for _index, row in self.phenotypes_df.iterrows():
            result[row['person_id']] = row.to_dict()
        return result

    def __repr__(self):
        return "PhenoResult: pvalue={:.3g}; pos={} (neg={})".format(
            self.pvalue, self.positive_count, self.negative_count)
