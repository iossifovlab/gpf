'''
Created on Dec 10, 2015

@author: lubo
'''
import numpy as np
from preloaded.register import Preload
from gene.weights import WeightsLoader


class Weights(Preload):

    def __init__(self):
        super(Weights, self).__init__()
        self.loader = WeightsLoader()

    def _load_desc(self):
        result = []

        for weight_name in self.loader.weights:
            w = self.loader[weight_name]
            assert w.df is not None

            bars, bins = np.histogram(w.values(), 150)
            result.append({"weight": w.name,
                           "desc": w.desc,
                           "min": float("{:.4G}".format(w.values().min())),
                           "max": float("{:.4G}".format(w.values().max())),
                           "bars": bars,
                           "bins": bins,
                           "step": w.step, })
        return result

    def load(self):
        self.desc = self._load_desc()

    def get(self):
        return self

    def has_weight(self, weight):
        return weight in self.loader

    def get_weight(self, weight):
        if weight not in self.loader:
            raise ValueError("unsupported gene weight {}".format(weight))

        return self.loader[weight]

    def get_genes_by_weight(self, weight, wmin=None, wmax=None):
        if weight not in self.loader:
            raise ValueError("unsupported gene weight {}".format(weight))
        w = self.loader[weight]
        genes = w.get_genes(wmin, wmax)
        return genes
