'''
Created on Nov 9, 2016

@author: lubo
'''

from scipy.stats.stats import ttest_ind

import numpy as np
import pandas as pd
import statsmodels.api as sm


class PhenoTool(object):
    """
    Tool to estimate dependency between variants and phenotype measrues.

    Receives as argument an instance of PhenoDB class.
    """

    def __init__(self, phdb):
        self.phdb = phdb

    def normalize_measure_values_df(self, measure_id, normalize_by=[]):
        """
        Returns a data frame containing values for the `measure_id`.

        Values are normalized if the argument `normalize_by` is a non empty
        list of measure_ids.
        """
        assert isinstance(normalize_by, list)
        assert all(map(lambda b: b in [
            'pheno_common.age', 'pheno_common.non_verbal_iq'], normalize_by))

        measures = normalize_by[:]
        measures.append(measure_id)

        df = self.phdb.get_persons_values_df(measures, role='prb')
        df.dropna(inplace=True)

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
    def _calc_stats(cls, data, gender):
        gender_index = data['gender'] == gender
        positive_index = np.logical_and(
            data['variants'] != 0, ~np.isnan(data['variants']))
        positive_gender_index = np.logical_and(
            positive_index, gender_index)

        negative_index = data['variants'] == 0
        negative_gender_index = np.logical_and(negative_index,
                                               gender_index)

        assert not np.any(np.logical_and(positive_gender_index,
                                         negative_gender_index))

        positive = data[positive_gender_index].normalized.values
        negative = data[negative_gender_index].normalized.values
        p_count, p_mean, p_std = PhenoTool._calc_base_stats(positive)
        n_count, n_mean, n_std = PhenoTool._calc_base_stats(negative)
        p_val = cls._calc_pv(positive, negative)

        return {
            'gender': gender,
            'negativeMean': n_mean,
            'negativeDeviation': n_std,
            'positiveMean': p_mean,
            'positiveDeviation': p_std,
            'pValue': p_val,
            'positiveCount': p_count,
            'negativeCount': n_count
        }

    def calc(self, families_variants, measure_id, normalize_by=[]):
        df = self.normalize_measure_values_df(measure_id, normalize_by)

        variants = pd.Series(0, index=df.index)
        df['variants'] = variants

        for index, row in df.iterrows():
            family_id = row['family_id']
            var_count = families_variants.get(family_id, 0)
            df.loc[index, 'variants'] = var_count

        result = []
        for gender in ['M', 'F']:
            p = self._calc_stats(df, gender)
            result.append(p)

        return result
