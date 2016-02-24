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
# import statsmodels.api as sm
from api.preloaded.register import Preload
from query_prepare import prepare_denovo_studies
from helpers.pvalue import colormap_value


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

    def _load_gender_all(self):
        stds = prepare_denovo_studies({'denovoStudies': ['IossifovWE2014',
                                                         'LevyCNV2011']})
        return {fmid: pd.gender for st in stds
                for fmid, fd in st.families.items()
                for pd in fd.memberInOrder if pd.role == 'prb'}

    def _load_gender_we(self):
        stds = prepare_denovo_studies({'denovoStudies': ['IossifovWE2014']})
        return {fmid: pd.gender for st in stds
                for fmid, fd in st.families.items()
                for pd in fd.memberInOrder if pd.role == 'prb'}

    def _load_gender_cnv(self):
        stds = prepare_denovo_studies({'denovoStudies': ['LevyCNV2011']})
        return {fmid: pd.gender for st in stds
                for fmid, fd in st.families.items()
                for pd in fd.memberInOrder if pd.role == 'prb'}

    def __init__(self):
        pass

    def load(self):
        self.df = self._load_data()
        self.desc = self._load_desc()
        self.gender_all = self._load_gender_all()
        self.gender_we = self._load_gender_we()
        self.gender_cnv = self._load_gender_cnv()

        self.measures = {}
        for m in self.desc:
            self.measures[m['measure']] = m

    def get(self):
        return self

    def has_measure(self, measure):
        return measure in self.measures

    def get_measure_df(self, measure):
        if measure not in self.measures:
            raise ValueError("unsupported phenotype measure")
        cols = ['family_id',
                'age', 'non_verbal_iq', 'verbal_iq']
        if measure not in cols:
            cols.append(measure)

        df = pd.DataFrame(index=self.df.index,
                          data=self.df[cols])
        df.dropna(inplace=True)
        return df

    def get_measure_families(self, measure, mmin=None, mmax=None):
        df = self.get_measure_df(measure)
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
        return selected['family_id'].values

    def pheno_merge_data(self, variants, nm):
        yield tuple(['family_id', 'gender',
                     'LGDs', 'recLGDs', 'missense', 'synonymous', 'CNV',
                     nm.measure, 'age', 'non_verbal_iq', nm.formula])
        for fid, gender in self.gender_all.items():
            vals = nm.df[nm.df.family_id == int(fid)]
            if len(vals) == 1:
                m = vals[nm.measure].values[0]
                v = vals.normalized.values[0]
                a = vals['age'].values[0]
                nviq = vals['non_verbal_iq'].values[0]
            else:
                m = np.NaN
                v = np.NaN
                a = np.NaN
                nviq = np.NaN

            cnv = variants[
                'CNV+,CNV-'].get(fid, 0) \
                if fid in self.gender_cnv else np.NaN
            lgds = variants[
                'LGDs'].get(fid, 0) \
                if fid in self.gender_we else np.NaN
            reclgds = variants[
                'LGDs.Rec'].get(fid, 0) \
                if fid in self.gender_we else np.NaN
            missense = variants[
                'missense'].get(fid, 0) \
                if fid in self.gender_we else np.NaN
            synonymous = variants[
                'synonymous'].get(fid, 0) \
                if fid in self.gender_we else np.NaN

            row = [fid, gender,
                   lgds, reclgds, missense, synonymous, cnv,
                   m, a, nviq, v]

            yield tuple(row)


class NormalizedMeasure(object):

    def __init__(self, measure):
        from api.preloaded.register import get_register
        self.measure = measure
        register = get_register()
        measures = register.get('pheno_measures')
        if not measures.has_measure(measure):
            raise ValueError("unknown phenotype measure")

        self.df = measures.get_measure_df(measure)
        self.by = []

    def normalize(self, by=[]):
        assert isinstance(by, list)
        assert all(map(lambda b: b in ['age', 'verbal_iq', 'non_verbal_iq'],
                       by))
        self.by = by

        if not by:
            # print(self.df[self.measure])
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
