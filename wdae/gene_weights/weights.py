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
        self.desc = None

    def is_loaded(self):
        return self.desc is not None

    def _load_desc(self):
        result = []

        for weight_name in self.loader.weights:
            w = self.loader[weight_name]
            assert w.df is not None

            step = (w.max() - w.min()) / (w.bins - 1)

            bars, bins = np.histogram(
                w.values(), w.bins,
                range=[w.min(), w.max() + step])
            # bins = np.round(bins, -int(np.log(step)))

            result.append({
                "weight": w.name,
                "desc": w.desc,
                "bars": bars,
                "bins": bins,
                "yscale": w.yscale
            })
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
