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

    def __getitem__(self, args):
        return self.config.get(*args)


class Weights(WeightsConfig):

    def __init__(self, weights_name, *args, **kwargs):
        super(Weights, self).__init__(*args, **kwargs)
        self.name = weights_name
        self.section_name = 'geneWeights.{}'.format(weights_name)
        self.desc = self[self.section_name, 'desc']
        self.df = None

    def load_weights(self):
        assert self[self.section_name, 'file'] is not None

        filename = self[self.section_name, 'file']
        assert filename is not None
        self.df = pd.read_csv(filename)
        assert self.name in self.df.columns

        return self.df

    def weights(self):
        return self.df[self.name]

    def get_genes(self, wmin=None, wmax=None):
        df = self.df[self.name]

        if wmin is None or wmin < df.min() or wmin > df.max():
            wmin = df.min()
        if wmax is None or wmax < df.min() or wmax > df.max():
            wmax = df.max()

        notnan_index = np.logical_not(np.isnan(df.values))
        minmax_index = np.logical_and(df.values >= wmin, df.values <= wmax)
        index = np.logical_and(notnan_index, minmax_index)

        genes = self.df[index].gene
        return set(genes.values)


class WeightsLoader(object):

    def __init__(self, *args, **kwargs):
        super(WeightsLoader, self).__init__(*args, **kwargs)
        self.config = WeightsConfig()
        self.weights = OrderedDict()
        self._load()

    def _load(self):
        weights = self.config['geneWeights', 'weights']
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
