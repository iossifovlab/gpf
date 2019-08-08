'''
Created on Nov 7, 2016

@author: lubo
'''
from collections import OrderedDict
import numpy as np

from gene.genomic_values import GenomicValues


class Weights(GenomicValues):
    """
    Represents gene weights.

    Loads a CSV file with gene weights by gene weight name as described
    in `geneInfo.conf`.
    """

    def __init__(self, config, *args, **kwargs):
        super(Weights, self).__init__(config.name, *args, **kwargs)
        self.config = config

        self.genomic_values_col = 'gene'

        self.desc = self.config.get('desc')
        self.bins = self.config.get('bins')
        self.xscale = self.config.get('xscale')
        self.yscale = self.config.get('yscale')
        self.filename = self.config.get('file')

        if 'range' in self.config:
            self.range = tuple(map(float, self.config.get('range')))
        else:
            self.range = None

        self._load_data()
        self.df.dropna(inplace=True)

        self.histogram_bins, self.histogram_bars = self.bins_bars()

    def bins_bars(self):
        step = 1.0 * (self.max() - self.min()) / (self.bins - 1)
        dec = - np.log10(step)
        dec = dec if dec >= 0 else 0
        dec = int(dec)

        bleft = np.around(self.min(), dec)
        bright = np.around(self.max() + step, dec)

        if self.xscale == "log":
            # Max numbers of items in first bin
            max_count = self.values().size / self.bins

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
    def load_gene_weights(name, config):
        """
        Creates and loads a gene weights instance by gene weights name.
        """
        assert name in Weights.list_gene_weights(config)
        weight_config = config.get(name)
        w = Weights(weight_config)
        return w

    @staticmethod
    def list_gene_weights(config):
        """
        Lists all available gene weights configured in `geneInfo.conf`.
        """
        weights = config.weights
        return weights


class WeightsLoader(object):
    """
    Helper class used to load all defined gene weights.

    Used by Web interface.
    """

    def __init__(self, config, *args, **kwargs):
        super(WeightsLoader, self).__init__(*args, **kwargs)
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
        weights = self.config.weights

        for weight in weights:
            weight_config = self.config.get(weight)
            w = Weights(weight_config)
            self.weights[weight] = w

    def __getitem__(self, weight_name):
        if weight_name not in self.weights:
            raise ValueError("unsupported gene weight {}".format(weight_name))

        res = self.weights[weight_name]
        if res.df is None:
            res.load_weights()
        return res

    def __contains__(self, weight_name):
        return weight_name in self.weights

    def __len__(self):
        return len(self.weights)
