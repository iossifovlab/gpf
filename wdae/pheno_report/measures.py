'''
Created on Nov 16, 2015

@author: lubo
'''
import os
import csv
import numpy as np
from django.conf import settings
import pandas as pd
import statsmodels.formula.api as sm
from preloaded.register import Preload
from helpers.pvalue import colormap_value
import precompute
import itertools
from pheno.models import VariableManager, PersonManager, ContinuousValueManager


class Measures(Preload):
    DESC_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/pheno/ssc_pheno_descriptions.csv')
    HELP_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/pheno/pheno_measures_help.csv')
    DATA_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/pheno/ssc_pheno_measures.csv')

    def _load_data(self):
        df = pd.read_csv(self.DATA_FILENAME)
        return df

    def _load_desc_only(self):
        result = []
        with open(self.DESC_FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                (measure, desc, norm_by_age,
                 norm_by_nviq,
                 norm_by_viq) = row[0:5]

                result.append({"measure": measure,
                               "desc": desc,
                               "normByAge": int(norm_by_age),
                               "normByNVIQ": int(norm_by_nviq),
                               "normByVIQ": int(norm_by_viq)})
        return result

    @staticmethod
    def _float_conv(val):
        if val == "NaN":
            return val
        else:
            return float(val)

    def _load_help(self):
        result = []
        with open(self.HELP_FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                (measure, hist, hist_small, measure_min, measure_max,
                 corr_by_age, corr_by_age_small,
                 age_coeff, age_p_val,
                 corr_by_nviq, corr_by_nviq_small,
                 nviq_coeff, nviq_p_val) = row
                result.append(
                    {"measure": measure,
                     "hist": hist,
                     "hist_small": hist_small,
                     "min": self._float_conv(measure_min),
                     "max": self._float_conv(measure_max),
                     "corr_age": corr_by_age,
                     "corr_age_small": corr_by_age_small,
                     "age_coeff": self._float_conv(age_coeff),
                     "age_p_val": self._float_conv(age_p_val),
                     "age_p_val_bg":
                     colormap_value(self._float_conv(age_p_val)),
                     "corr_nviq": corr_by_nviq,
                     "corr_by_nviq_small": corr_by_nviq_small,
                     "nviq_coeff": self._float_conv(nviq_coeff),
                     "nviq_p_val": self._float_conv(nviq_p_val),
                     "nviq_p_val_bg":
                     colormap_value(self._float_conv(nviq_p_val)),
                     })
        return result

    def _load_desc(self):
        desc = self._load_desc_only()
        pheno_help = self._load_help()

        result = []
        for d, h in zip(desc, pheno_help):
            assert d['measure'] == h['measure'], "{}: {}".format(
                d['measure'], h['measure'])
            r = dict(d)
            r.update(h)
            result.append(r)
        return result

    def __init__(self):
        pass

    def load(self):
        # self.df = self._load_data()
        self.desc = self._load_desc()
        self.families_precompute = precompute.register.get(
            'pheno_families_precompute')
        # self.probands_gender = families_precompute.probands_gender()
        self.probands_gender = \
            zip(itertools.cycle(['M']),
                self.families_precompute.probands('M'))
        self.probands_gender.extend(
            zip(itertools.cycle(['F']),
                self.families_precompute.probands('F')))
        # self.measures = {}
        # for m in self.desc:
        #     self.measures[m['measure']] = m

    def get(self):
        return self

    def has_measure(self, instrument, measure):
        if measure in set(['non_verbal_iq', 'verbal_iq']):
            return True
        measure_id = '{}.{}'.format(instrument, measure)
        with VariableManager() as vm:
            variable = vm.get(
                where="variable_id='{}' and stats='continuous'"
                .format(measure_id))
        return variable is not None

    def get_measure_df(self, instrument, measure):
        if not self.has_measure(instrument, measure):
            raise ValueError("unsupported phenotype measure")

        with PersonManager() as pm:
            persons_df = pm.load_df(where="role='prb' and ssc_present=1")

        if measure in set(['non_verbal_iq', 'verbal_iq']):
            return persons_df.dropna()

        measure_id = '{}.{}'.format(instrument, measure)
        with ContinuousValueManager() as vm:
            value_df = vm.load_df(where="variable_id='{}'".format(measure_id))

        df = persons_df.set_index('person_id').join(
            value_df.set_index('person_id'), rsuffix='_val')
        res_df = df.dropna()

        names = res_df.columns.tolist()
        names[names.index('value')] = measure
        res_df.columns = names

        return res_df

    def _select_measure_df(self, instrument, measure, mmin, mmax):
        df = self.get_measure_df(instrument, measure)
        m = df[measure]
        selected = None
        if mmin is not None and mmax is not None:
            selected = df[np.logical_and(m >= mmin, m <= mmax)]
        elif mmin is not None:
            selected = df[m >= mmin]
        elif mmax is not None:
            selected = df[m <= mmax]
        else:
            selected = df
        return selected

    def get_measure_families(self, instrument, measure, mmin=None, mmax=None):
        selected = self._select_measure_df(instrument, measure, mmin, mmax)
        return selected['family_id'].values

    def get_measure_probands(self, instrument, measure, mmin=None, mmax=None):
        selected = self._select_measure_df(instrument, measure, mmin, mmax)
        return selected['individual'].values


#     def pheno_merge_data(self, families_with_variants,
#                          nm,
#                          effect_type_groups,
#                          families_query=None):
#         columns = ['family_id', 'person_id', 'gender', ]
#         columns.extend(effect_type_groups)
#         columns.extend([nm.measure, 'age', 'non_verbal_iq', nm.formula])
#         yield tuple(columns)
#
#         for gender, pid in self.probands_gender:
#             fid = pheno_filter.FamilyFilter.strip_proband_id(pid)
#             if families_query is not None and fid not in families_query:
#                 continue
#             vals = nm.df[nm.df.family_id == int(fid)]
#             if len(vals) == 1:
#                 m = vals[nm.measure].values[0]
#                 v = vals.normalized.values[0]
#                 a = vals['age'].values[0]
#                 nviq = vals['non_verbal_iq'].values[0]
#             else:
#                 m = np.NaN
#                 v = np.NaN
#                 a = np.NaN
#                 nviq = np.NaN
#
#             row = [fid, pid, gender, ]
#             for etg in effect_type_groups:
#                 if pid in self.families_precompute.probands(gender):
#                     col = families_with_variants[etg].get(fid, 0)
#                 else:
#                     col = np.NaN
#                 row.append(col)
#
#             row.extend([m, a, nviq, v])
#             yield tuple(row)


class NormalizedMeasure(object):

    def __init__(self, instrument, measure):
        from preloaded.register import get_register
        self.measure = measure
        self.instrument = instrument
        register = get_register()
        measures = register.get('pheno_measures')
        if not measures.has_measure(instrument, measure):
            raise ValueError("unknown phenotype measure")

        self.df = measures.get_measure_df(instrument, measure)
        self.by = []

    def normalize(self, by=[]):
        assert isinstance(by, list)
        assert all(map(lambda b: b in ['age', 'verbal_iq', 'non_verbal_iq'],
                       by))
        self.by = by

        if not by:
            dn = pd.Series(
                index=self.df.index, data=self.df[self.measure].values)
            self.df['normalized'] = dn
            self.formula = self.measure

        else:
            self.formula = '{} ~ {}'.format(self.measure, ' + '.join(by))
            model = sm.ols(formula=self.formula,
                           data=self.df)
            fitted = model.fit()
            dn = pd.Series(index=self.df.index, data=fitted.resid)
            self.df['normalized'] = dn
            return self.df
