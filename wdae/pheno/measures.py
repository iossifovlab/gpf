'''
Created on Nov 16, 2015

@author: lubo
'''
import os
import csv
from django.conf import settings
import pandas as pd
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
        self.df = self._load_data()
        self.desc = self._load_desc()

    def load(self):
        self.df = self._load_data()
        self.desc = self._load_desc()

    def get(self):
        return self.desc, self.df


class NormalizedMeasures(object):
    pass
