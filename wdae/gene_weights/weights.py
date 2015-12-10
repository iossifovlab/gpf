'''
Created on Dec 10, 2015

@author: lubo
'''
import os
import csv
import pandas as pd
from api.preloaded.register import Preload
from django.conf import settings


class Weights(Preload):
    DESC_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/gene_weights/gene_weights_description.csv')
    DATA_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/gene_weights/gene_weights.csv')

    def _load_data(self):
        df = pd.read_csv(self.DATA_FILENAME)
        return df

    def _load_desc(self):
        result = []
        with open(self.DESC_FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                (weight, desc, use) = row
                use = int(use)
                if not use:
                    continue
                result.append({"weight": weight,
                               "desc": desc})
        return result

    def load(self):
        self.df = self._load_data()
        self.desc = self._load_desc()
        self.weights = {}
        for w in self.desc:
            self.weights[w['weight']] = w

    def get(self):
        return self

    def has_weight(self, weight):
        return weight in self.weights

    def get_weight(self, weight):
        if weight not in self.weights:
            raise ValueError("unsupported gene weight")

        return self.df[weight]
