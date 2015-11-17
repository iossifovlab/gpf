'''
Created on Nov 16, 2015

@author: lubo
'''
import os
import csv
from django.conf import settings
import pandas as pd
import statsmodels.formula.api as sm
from api.preloaded.register import Preload


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
                               "norm_by_age": int(norm_by_age),
                               "norm_by_nviq": int(norm_by_nviq),
                               "norm_by_viq": int(norm_by_viq)})
        return result

    def __init__(self):
        pass

    def load(self):
        self.df = self._load_data()
        self.desc = self._load_desc()
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
        df = pd.DataFrame(index=self.df.index,
                          data=self.df[[measure,
                                        'family_id',
                                        'age', 'non_verbal_iq', 'verbal_iq']])
        df.dropna(inplace=True)
        return df


class NormalizedMeasure(object):

    def __init__(self, measure):
        from api.preloaded.register import get_register
        self.measure = measure
        register = get_register()
        measures = register.get('pheno_measures')
        if not measures.has_measure(measure):
            raise ValueError("unknown phenotype measure")

        self.df = measures.get_measure_df(measure)

    def normalize(self, by=['age']):
        assert isinstance(by, list)

        x = ' + '.join(by)
        model = sm.ols(formula='{} ~ {}'.format(self.measure, x),
                       data=self.df)

        fitted = model.fit()
        print fitted.summary()
        return fitted
