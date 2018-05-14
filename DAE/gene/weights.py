'''
Created on Nov 7, 2016

@author: lubo
'''

from builtins import object
from collections import OrderedDict

import numpy as np
import pandas as pd
from gene.config import GeneInfoConfig


class Weights(GeneInfoConfig):
    """
    Represents gene weights.

    Loads a CSV file with gene weights by gene weight name as described
    in `geneInfo.conf`.
    """

    def __init__(self, weights_name, *args, **kwargs):
        super(Weights, self).__init__(*args, **kwargs)
        self.name = weights_name
        self.section_name = 'geneWeights.{}'.format(weights_name)
        self.desc = self.config.get(self.section_name, 'desc')
        self.bins = int(self.config.get(self.section_name, 'bins'))
        self.xscale = self.config.get(self.section_name, 'xscale')
        self.yscale = self.config.get(self.section_name, 'yscale')

        self.df = None
        self._dict = None
        self._load_weights()

    def _load_weights(self):
        assert self.config.get(self.section_name, 'file') is not None

        filename = self.config.get(self.section_name, 'file')
        assert filename is not None
        df = pd.read_csv(filename)
        assert self.name in df.columns

        self.df = df[['gene', self.name]].copy()
        self.df.dropna(inplace=True)

        return self.df

    def min(self):
        """
        Returns minimal weight value.
        """
        return self.df[self.name].min()

    def max(self):
        """
        Returns maximal weight value.
        """
        return self.df[self.name].max()

    def get_genes(self, wmin=None, wmax=None):
        """
        Returns a set of genes which weights are between `wmin` and `wmax`.

        `wmin` -- the lower bound of weights. If not specified or `None`
        works without lower bound.

        `wmax` -- the upper bound of weights. If not specified or `None`
        works without upper bound.
        """
        df = self.df[self.name]
        df.dropna(inplace=True)

        if wmin is None or wmin < df.min() or wmin > df.max():
            wmin = float("-inf")
        if wmax is None or wmax < df.min() or wmax > df.max():
            wmax = float("inf")

        index = np.logical_and(df.values >= wmin, df.values < wmax)
        genes = self.df[index].gene
        return set(genes.values)

    def to_dict(self):
        """
        Returns dictionary of all defined weights keyed by gene symbol.
        """
        if self._dict is None:
            self._dict = self.df.set_index('gene')[self.name].to_dict()
        return self._dict

    def to_df(self):
        """
        Returns a data frame with all gene weights with columns `gene` and
        `weight`.
        """
        return self.df

    def values(self):
        return self.df[self.name].values

    @staticmethod
    def load_gene_weights(name):
        """
        Creates and loads a gene weights instance by gene weights name.
        """
        assert name in Weights.list_gene_weights()
        w = Weights(name)
        return w


class WeightsLoader(object):
    """
    Helper class used to load all defined gene weights.

    Used by Web interface.
    """

    def __init__(self, *args, **kwargs):
        super(WeightsLoader, self).__init__(*args, **kwargs)
        self.config = GeneInfoConfig()
        self.weights = OrderedDict()
        self._load()

    def _load(self):
        weights = self.config.config.get('geneWeights', 'weights')
        names = [n.strip() for n in weights.split(',')]
        for name in names:
            w = Weights(name)
            self.weights[name] = w

    def __getitem__(self, weights_name):
        if weights_name not in self.weights:
            raise KeyError()

        res = self.weights[weights_name]
        if res.df is None:
            res.load_weights()
        return res

    def __contains__(self, weights_name):
        return weights_name in self.weights
