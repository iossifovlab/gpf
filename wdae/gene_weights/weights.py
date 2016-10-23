'''
Created on Dec 10, 2015

@author: lubo
'''
import os
import csv
import pandas as pd
import numpy as np
from preloaded.register import Preload
from django.conf import settings


class Weights(Preload):
    DESC_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/gene_weights/gene_weights_description.csv')
    DATA_FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/gene_weights/gene_weights_2.csv')

    def _load_data(self):
        df = pd.read_csv(self.DATA_FILENAME)
        return df

    def _load_desc(self, df):
        result = []
        with open(self.DESC_FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                (weight, desc, use, step) = row
                use = int(use)
                if not use:
                    continue
                w = df[weight]
                bars, bins = np.histogram(
                    w[np.logical_not(np.isnan(w.values))].values, 150)
                result.append({"weight": weight,
                               "desc": desc,
                               "min": float("{:.4G}".format(w.min())),
                               "max": float("{:.4G}".format(w.max())),
                               "bars": bars,
                               "bins": bins,
                               "step": step, })
        return result

    def load(self):
        self.df = self._load_data()
        self.desc = self._load_desc(self.df)
        self.weights = {}
        for w in self.desc:
            self.weights[w['weight']] = w

    def get(self):
        return self

    def has_weight(self, weight):
        return weight in self.weights

    def get_weight(self, weight):
        if weight not in self.weights:
            raise ValueError("unsupported gene weight {}".format(weight))

        return self.df[weight]

    def get_genes_by_weight(self, weight, wmin=None, wmax=None):
        if weight not in self.weights:
            raise ValueError("unsupported gene weight {}".format(weight))
        df = self.df[weight]

        if wmin is None or wmin < df.min() or wmin > df.max():
            wmin = df.min()
        if wmax is None or wmax < df.min() or wmax > df.max():
            wmax = df.max()

        notnan_index = np.logical_not(np.isnan(df.values))
        print("NOTNAN: ", np.sum(notnan_index))
        minmax_index = np.logical_and(df.values >= wmin, df.values <= wmax)
        index = np.logical_and(notnan_index, minmax_index)
        print("INDEX: ", np.sum(index))

        genes = self.df[index].gene
        return set(genes.values)
