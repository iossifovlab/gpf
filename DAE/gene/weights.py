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

    def __init__(self, *args, **kwargs):
        super(WeightsConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        self.config = ConfigParser.SafeConfigParser({'wd': wd})
        self.config.read(self.dae_config.geneInfoDBconfFile)

#     def __getitem__(self, args):
#         return self.config.get(*args)


class Weights(WeightsConfig):

    def __init__(self, weights_name, *args, **kwargs):
        super(Weights, self).__init__(*args, **kwargs)
        self.name = weights_name
        self.section_name = 'geneWeights.{}'.format(weights_name)
        self.desc = self.config.get(self.section_name, 'desc')
        self.step = self.config.get(self.section_name, 'step')
        self.df = None

    def load_weights(self):
        assert self.config.get(self.section_name, 'file') is not None

        filename = self.config.get(self.section_name, 'file')
        assert filename is not None
        df = pd.read_csv(filename)
        assert self.name in df.columns

        self.df = df[['gene', self.name]].copy()
        self.df.dropna(inplace=True)

        return self.df

    def weights(self):
        return self.df[self.name]

    def min(self):
        return self.df[self.name].min()

    def max(self):
        return self.df[self.name].max()

    def get_genes(self, wmin=None, wmax=None):
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
        result = {}
        for _index, row in self.df.iterrows():
            result[row['gene']] = row[self.name]
        return result


class WeightsLoader(object):

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
