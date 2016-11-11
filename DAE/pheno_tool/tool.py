'''
Created on Nov 9, 2016

@author: lubo
'''
from collections import Counter
import itertools

from scipy.stats.stats import ttest_ind

import numpy as np
from pheno_tool.measures import NormalizedMeasure
from query_variants import dae_query_families_with_variants


class PhenoRequest(object):

    def __init__(self, effect_type_groups=['LGDs'],
                 in_child='prb',
                 present_in_parent='neither'):
        self.effect_type_groups = effect_type_groups
        self.in_child = in_child
        self.present_in_parent = present_in_parent

    def dae_query_request(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'presentInParent': self.present_in_parent,
            'inChild': self.in_child,
            'effectTypes': self.effect_type_groups,

        }
        return data


class PhenoTool(object):

    DEFAULT_STUDY = 'ALL SSC'
    DEFAULT_TRANSMITTED = ''

    def __init__(self, measures,
                 study=DEFAULT_STUDY,
                 transmitted=DEFAULT_TRANSMITTED):
        self.measures = measures
        self.study = study
        self.transmitted = transmitted

    def build_families_variants(self, request):
        result = {}
        for effect_type in request.effect_type_groups:
            data = request.dae_query_request()
            data['effectTypes'] = effect_type
            data['inChild'] = 'prb'

            fams = dae_query_families_with_variants(data)
            result[effect_type] = Counter(fams)

        return result

    def build_table_header(self, pheno_request, normalized_measure):
        columns = ['family_id', 'person_id', 'gender', ]
        columns.extend(pheno_request.effect_type_groups)
        columns.extend([
            normalized_measure.measure_id,
            'pheno_common.age',
            'pheno_common.non_verbal_iq',
            normalized_measure.formula
        ])
        return tuple(columns)

    @staticmethod
    def strip_proband_id(proband_id):
        return proband_id.split('.')[0]

    def _build_table_row(self, person_id, gender):
        family_id = self.strip_proband_id(person_id)
        vals = self.nm.df[self.nm.df.person_id == person_id]
        if len(vals) == 1:
            m = vals[self.nm.measure_id].values[0]
            v = vals.normalized.values[0]
            a = vals['pheno_common.age'].values[0]
            nviq = vals['pheno_common.non_verbal_iq'].values[0]
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

    def build_data_table(self, pheno_request, normalized_measure):
        self.build_families_variants(pheno_request)

        header = self.build_table_header(pheno_request, normalized_measure)
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

    def build_data_array(self, pheno_request, normalized_measure):
        gen = self.build_data_table(pheno_request, normalized_measure)
        gen.next()  # skip table header
        rows = []
        for row in gen:
            rows.append(tuple([v if v != 'NA' else np.NaN for v in row]))
        dtype = self._build_narray_dtype()
        result = np.array(rows, dtype=dtype)

        # print(result[np.isnan(result['value'])])
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

    def calc(self, pheno_request, measure_id, normalized_by=None):
        effect_type_groups = pheno_request['effect_type_groups']
        normalized_measure = NormalizedMeasure(self.measures, measure_id)
        normalized_measure.normalize(normalized_by)

        result = []
        data = self.build_data_array(pheno_request, normalized_measure)

        for eff, gender in itertools.product(
                *[effect_type_groups, ['M', 'F']]):
            p = self._calc_stats(data, eff, gender)
            result.append(p)

        return result
