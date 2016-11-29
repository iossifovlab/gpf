'''
Created on Nov 7, 2016

@author: lubo
'''

import ConfigParser
from collections import OrderedDict

from Config import Config
import numpy as np
import pandas as pd


class WeightsConfig(object):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, *args, **kwargs):
        super(WeightsConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        self.config = ConfigParser.SafeConfigParser({'wd': wd})
        self.config.read(self.dae_config.geneInfoDBconfFile)


class Weights(WeightsConfig):
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
        self.step = self.config.get(self.section_name, 'step')
        self.df = None
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

#     def weights(self):
#         return self.df[self.name]

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
            wmin = df.min()
        if wmax is None or wmax < df.min() or wmax > df.max():
            wmax = df.max()

        index = np.logical_and(df.values >= wmin, df.values <= wmax)
        genes = self.df[index].gene
        return set(genes.values)

    def to_dict(self):
        """
        Returns dictionary of all defined weights keyed by gene symbol.
        """
        result = {}
        for _index, row in self.df.iterrows():
            result[row['gene']] = row[self.name]
        return result

    def to_df(self):
        """
        Returns a data frame with all gene weights with columns `gene` and
        `weight`.
        """
        return self.df

    def values(self):
        return self.df[self.name].values

    @staticmethod
    def list_gene_weights():
        """
        Lists all available gene weights configured in `geneInfo.conf`.
        """
        dae_config = Config()
        wd = dae_config.daeDir
        config = ConfigParser.SafeConfigParser({'wd': wd})
        config.read(dae_config.geneInfoDBconfFile)

        weights = config.get('geneWeights', 'weights')
        names = [n.strip() for n in weights.split(',')]
        return names

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
        self.config = WeightsConfig()
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
