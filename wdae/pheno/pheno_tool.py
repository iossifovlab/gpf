'''
Created on Aug 9, 2016

@author: lubo
'''
import copy
from collections import Counter
from query_variants import dae_query_families_with_variants
import precompute
from pheno_families import pheno_filter
import numpy as np
import itertools
from scipy.stats.stats import ttest_ind


class PhenoTool(object):

    def __init__(self, req):
        self.req = req
        self.effect_type_groups = req.effect_type_groups
        self.data = req.data
        self.probands = req.probands
        self.families = req.families
        self.nm = req.nm
        self.pheno_families = precompute.register.get(
            'pheno_families_precompute')

    def _build_families_variants(self):
        result = {}
        for effect_type in self.effect_type_groups:
            data = copy.deepcopy(self.data)
            data['effectTypes'] = effect_type
            data['inChild'] = 'prb'

            fams = dae_query_families_with_variants(data)
            result[effect_type] = Counter(fams)

        self._families_variants = result
        return result

    def _build_table_header(self):
        columns = ['family_id', 'person_id', 'gender', ]
        columns.extend(self.effect_type_groups)
        columns.extend(
            [self.nm.measure, 'age', 'non_verbal_iq', self.nm.formula])
        return tuple(columns)

    def _build_table_row(self, person_id, gender):
        family_id = pheno_filter.FamilyFilter.strip_proband_id(person_id)
        vals = self.nm.df[self.nm.df.individual == person_id]
        if len(vals) == 1:
            m = vals[self.nm.measure].values[0]
            v = vals.normalized.values[0]
            a = vals['age'].values[0]
            nviq = vals['non_verbal_iq'].values[0]
        else:
            m = np.NaN
            v = np.NaN
            a = np.NaN
            nviq = np.NaN
        row = [family_id, person_id, gender]
        for etg in self.effect_type_groups:
            col = self._families_variants[etg].get(family_id, 0)
            row.append(col)

        row.extend([m, a, nviq, v])
        return row

    def _build_data_table(self):
        self._build_families_variants()

        header = self._build_table_header()
        yield header

        for gender, person_id in self.pheno_families.probands_gender():
            if person_id not in self.probands:
                continue

            row = self._build_table_row(person_id, gender)
            yield tuple(row)

    def _build_narray_dtype(self):
        columns = [('fid', 'S10'),
                   ('pid', 'S13'),
                   ('gender', 'S10'), ]
        for eff in self.effect_type_groups:
            columns.append((eff, 'f'))

        columns.extend(
            [('measure', 'f'),
             ('age', 'f'),
             ('non_verbal_iq', 'f'),
             ('value', 'f')])

        return np.dtype(columns)

    def _build_data_array(self):
        gen = self._build_data_table()
        gen.next()  # skip table header
        rows = []
        for row in gen:
            rows.append(tuple([v if v != 'NA' else np.NaN for v in row]))
        dtype = self._build_narray_dtype()
        result = np.array(rows, dtype=dtype)

        print(result[np.isnan(result['value'])])
        assert not np.any(np.isnan(result['value']))

        return result

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
        if np.isnan(pv):
            return "NA"
        if pv >= 0.1:
            return "%.1f" % (pv)
        if pv >= 0.01:
            return "%.2f" % (pv)
        if pv >= 0.001:
            return "%.3f" % (pv)
        if pv >= 0.0001:
            return "%.4f" % (pv)
        return "%.5f" % (pv)

    @staticmethod
    def _calc_stats(data, eff, gender):
        gender_index = data['gender'] == gender
        positive_index = np.logical_and(
            data[eff] != 0, ~np.isnan(data[eff]))
        positive_gender_index = np.logical_and(
            positive_index, gender_index)

        negative_index = data[eff] == 0
        negative_gender_index = np.logical_and(negative_index,
                                               gender_index)

        assert not np.any(np.logical_and(positive_gender_index,
                                         negative_gender_index))

        positive = data[positive_gender_index]['value']
        negative = data[negative_gender_index]['value']
        p_count, p_mean, p_std = PhenoTool._calc_base_stats(positive)
        n_count, n_mean, n_std = PhenoTool._calc_base_stats(negative)
        p_val = PhenoTool._calc_pv(positive, negative)

        return {
            'effectType': eff,
            'gender': gender,
            'negativeMean': n_mean,
            'negativeDeviation': n_std,
            'positiveMean': p_mean,
            'positiveDeviation': p_std,
            'pValue': p_val,
            'positiveCount': p_count,
            'negativeCount': n_count
        }

    def calc(self):
        result = []
        data = self._build_data_array()

        for eff, gender in itertools.product(
                *[self.effect_type_groups, ['M', 'F']]):
            p = self._calc_stats(data, eff, gender)
            result.append(p)

        return result

    def counters(self):
        return self.req.pheno_counters(self.probands)
