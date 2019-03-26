'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()  # noqa

from builtins import object
from configparser import ConfigParser
from collections import OrderedDict
from past.utils import old_div

import numpy as np
from gene.genomic_values import GenomicValues
from gene.config import GeneInfoConfig
from Config import Config


class Weights(GenomicValues):
    """
    Represents gene weights.

    Loads a CSV file with gene weights by gene weight name as described
    in `geneInfo.conf`.
    """

    def __init__(self, weights_name, *args, **kwargs):
        super(Weights, self).__init__('geneWeights.{}'.format(weights_name),
                                      *args, **kwargs)

        self.config = GeneInfoConfig()

        self.genomic_values_col = 'gene'

        self.desc = self.config.config.get(self.section_name, 'desc')
        self.bins = int(self.config.config.get(self.section_name, 'bins'))
        self.xscale = self.config.config.get(self.section_name, 'xscale')
        self.yscale = self.config.config.get(self.section_name, 'yscale')
        self.filename = self.config.config.get(self.section_name, 'file')

        if self.config.config.has_option(self.section_name, 'range'):
            self.range = tuple(map(float, self.config.config.get(
                self.section_name, 'range').split(',')))
        else:
            self.range = None

        self._load_data()
        self.df.dropna(inplace=True)

        self.histogram_bins, self.histogram_bars = self.bins_bars()

    def bins_bars(self):
        step = old_div((self.max() - self.min()), (self.bins - 1))
        dec = - np.log10(step)
        dec = dec if dec >= 0 else 0
        dec = int(dec)

        bleft = np.around(self.min(), dec)
        bright = np.around(self.max() + step, dec)

        if self.xscale == "log":
            # Max numbers of items in first bin
            max_count = old_div(self.values().size, self.bins)

            # Find a bin small enough to fit max_count items
            for bleft in range(-1, -200, -1):
                if ((self.values()) < 10 ** bleft).sum() < max_count:
                    break

            bins_in = [0] + list(np.logspace(bleft, np.log10(bright),
                                             self.bins))
        else:
            bins_in = self.bins

        bars, bins = np.histogram(
            list(self.values()), bins_in,
            range=[bleft, bright])
        # bins = np.round(bins, -int(np.log(step)))

        return (bins, bars)

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

    @staticmethod
    def list_gene_weights():
        """
        Lists all available gene weights configured in `geneInfo.conf`.
        """
        dae_config = Config()
        wd = dae_config.daeDir
        data_dir = dae_config.data_dir

        config = ConfigParser({
            'wd': wd,
            'data': data_dir,
        })
        config.read(dae_config.geneInfoDBconfFile)

        weights = config.get('geneWeights', 'weights')
        names = [n.strip() for n in weights.split(',')]
        return names


class WeightsLoader(object):
    """
    Helper class used to load all defined gene weights.

    Used by Web interface.
    """

    def __init__(self, config=None, *args, **kwargs):
        super(WeightsLoader, self).__init__(*args, **kwargs)
        if config is None:
            config = GeneInfoConfig()
        self.config = config

        self.weights = OrderedDict()
        self._load()

    def get_weights(self):
        result = []

        for weight_name in self.weights:
            weight = self[weight_name]

            assert weight.df is not None

            result.append(weight)

        return result

    def _load(self):
        weights = self.config.config.get('geneWeights', 'weights')
        if weights == '':
            return

        names = [n.strip() for n in weights.split(',')]
        for name in names:
            w = Weights(name)
            self.weights[name] = w

    def __getitem__(self, weight_name):
        if weight_name not in self.weights:
            raise ValueError("unsupported gene weight {}".format(weight_name))

        res = self.weights[weight_name]
        if res.df is None:
            res.load_weights()
        return res

    def __contains__(self, weight_name):
        return weight_name in self.weights
