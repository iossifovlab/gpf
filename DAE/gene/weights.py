'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np
from collections import OrderedDict

from data import Data
from gene.config import GeneInfoConfig


class Weights(Data, GeneInfoConfig):
    """
    Represents gene weights.

    Loads a CSV file with gene weights by gene weight name as described
    in `geneInfo.conf`.
    """

    def __init__(self, weights_name, *args, **kwargs):
        GeneInfoConfig.__init__(self, *args, **kwargs)

        self.section_name = 'geneWeights.{}'.format(weights_name)
        self.data_col = 'gene'

        self.desc = self.config.get(self.section_name, 'desc')
        self.bins = int(self.config.get(self.section_name, 'bins'))
        self.xscale = self.config.get(self.section_name, 'xscale')
        self.yscale = self.config.get(self.section_name, 'yscale')
        self.filename = self.config.get(self.section_name, 'file')

        Data.__init__(self, *args, **kwargs)

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

    def __getitem__(self, weight_name):
        if weight_name not in self.weights:
            raise KeyError()

        res = self.weights[weight_name]
        if res.df is None:
            res.load_weights()
        return res

    def __contains__(self, weight_name):
        return weight_name in self.weights
