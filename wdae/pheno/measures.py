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


class Measures(Preload):
    DESC_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/pheno/ssc_pheno_descriptions.csv')
    DATA_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/pheno/ssc_pheno_measures.csv')

    def _load_data(self):
        df = pd.read_csv(self.DATA_FILENAME)
        return df

    def _load_desc(self):
        result = []
        with open(self.DESC_FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                (measure, desc, norm_by_age,
                 norm_by_nviq,
                 norm_by_viq) = row

                result.append({"measure": measure,
                               "desc": desc,
                               "normByAge": int(norm_by_age),
                               "normByNVIQ": int(norm_by_nviq),
                               "normByVIQ": int(norm_by_viq)})
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

    def pheno_merge_data(self, variants, nm):
        yield tuple(['family_id', 'gender', 'LGDs', 'recLGDs', 'missense',
                     'synonymous', 'CNV', nm.measure, 'age',
                     'non_verbal_iq', nm.formula])
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

            row = [fid, gender, lgds, reclgds, missense, synonymous, cnv,
                   a, nviq, m, v]

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
