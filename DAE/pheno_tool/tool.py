'''
Created on Nov 9, 2016

@author: lubo
'''
from collections import Counter
import itertools

from scipy.stats.stats import ttest_ind

import numpy as np
import pandas as pd
from query_variants import dae_query_families_with_variants
import statsmodels.api as sm

DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class PhenoRequest(object):

    def __init__(self, effect_type_groups=['LGDs'],
                 in_child='prb',
                 present_in_parent='neither',
                 study=DEFAULT_STUDY,
                 transmitted=DEFAULT_TRANSMITTED):
        self.study = study
        self.transmitted = transmitted
        self.effect_type_groups = effect_type_groups
        self.in_child = in_child
        self.present_in_parent = present_in_parent
        self.probands = None

    def dae_query_request(self):
        data = {
            'denovoStudies': self.study,
            'transmittedStudies': self.transmitted,
            'presentInParent': self.present_in_parent,
            'inChild': self.in_child,
            'effectTypes': self.effect_type_groups,
        }
        return data


class PhenoTool(object):

    def __init__(self, phdb):
        self.phdb = phdb

    def normalize_measure_values_df(self, measure_id, by=[]):
        assert isinstance(by, list)
        assert all(map(lambda b: b in [
            'pheno_common.age', 'pheno_common.non_verbal_iq'], by))

        measures = by[:]
        measures.append(measure_id)

        df = self.phdb.get_persons_values_df(measures, role='prb')
        df.dropna(inplace=True)

        if not by:
            dn = pd.Series(
                index=df.index, data=df[measure_id].values)
            df['normalized'] = dn
            return df
        else:
            X = sm.add_constant(df[by])
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
    def _calc_stats(cls, data, effect_type, gender):
        gender_index = data['gender'] == gender
        positive_index = np.logical_and(
            data[effect_type] != 0, ~np.isnan(data[effect_type]))
        positive_gender_index = np.logical_and(
            positive_index, gender_index)

        negative_index = data[effect_type] == 0
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
            'effectType': effect_type,
            'gender': gender,
            'negativeMean': n_mean,
            'negativeDeviation': n_std,
            'positiveMean': p_mean,
            'positiveDeviation': p_std,
            'pValue': p_val,
            'positiveCount': p_count,
            'negativeCount': n_count
        }

    def _build_families_variants(self, pheno_request):
        result = {}
        for effect_type in pheno_request.effect_type_groups:
            data = pheno_request.dae_query_request()
            data['effectTypes'] = effect_type
            data['inChild'] = 'prb'

            fams = dae_query_families_with_variants(data)
            result[effect_type] = Counter(fams)

        return result

    def calc(self, pheno_request, measure_id, normalize_by=[]):
        df = self.normalize_measure_values_df(measure_id, normalize_by)
        families_variants = self._build_families_variants(pheno_request)
        for effect_type in pheno_request.effect_type_groups:
            et = pd.Series(0, index=df.index)
            df[effect_type] = et

        for index, row in df.iterrows():
            family_id = row['family_id']
            for effect_type in pheno_request.effect_type_groups:
                var_count = families_variants[effect_type].get(family_id, 0)
                df.loc[index, effect_type] = var_count

        result = []
        for effect_type, gender in itertools.product(
                *[pheno_request.effect_type_groups, ['M', 'F']]):
            p = self._calc_stats(df, effect_type, gender)
            result.append(p)

        return result
