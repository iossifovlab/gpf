import itertools
from collections import OrderedDict, namedtuple
import numpy as np

from dae.gene.genomic_values import GenomicValues
from dae.utils.dae_utils import join_line


class GeneWeight(GenomicValues):
    """
    Represents gene weights.

    Loads a CSV file with gene weights by gene weight id as described
    in `geneInfo.conf`.
    """

    def __init__(self, config):
        super(GeneWeight, self).__init__(config.id)
        self.config = config

        self.genomic_values_col = 'gene'

        self.desc = self.config.desc
        self.bins = self.config.bins
        self.xscale = self.config.xscale
        self.yscale = self.config.yscale
        self.filename = self.config.file
        self.range = self.config.range

        self._load_data()
        self.df.dropna(inplace=True)

        self.histogram_bins, self.histogram_bars = self._bins_bars()

    def _bins_bars(self):
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

    def _to_dict(self):
        """
        Returns dictionary of all defined weights keyed by gene symbol.
        """
        if self._dict is None:
            self._dict = self.df.set_index('gene')[self.id].to_dict()
        return self._dict

    def _to_list(self):
        columns = self.df.applymap(str).columns.tolist()
        values = self.df.applymap(str).values.tolist()

        return itertools.chain([columns], values)

    def _to_tsv(self):
        return map(join_line, self.to_list())

    def min(self):
        """
        Returns minimal weight value.
        """
        return self.df[self.id].min()

    def max(self):
        """
        Returns maximal weight value.
        """
        return self.df[self.id].max()

    def get_genes(self, wmin=None, wmax=None):
        """
        Returns a set of genes which weights are between `wmin` and `wmax`.

        `wmin` -- the lower bound of weights. If not specified or `None`
        works without lower bound.

        `wmax` -- the upper bound of weights. If not specified or `None`
        works without upper bound.
        """
        df = self.df[self.id]
        df.dropna(inplace=True)

        if wmin is None or wmin < df.min() or wmin > df.max():
            wmin = float("-inf")
        if wmax is None or wmax < df.min() or wmax > df.max():
            wmax = float("inf")

        index = np.logical_and(df.values >= wmin, df.values < wmax)
        genes = self.df[index].gene
        return set(genes.values)


class GeneWeightsDb(object):
    """
    Helper class used to load all defined gene weights.

    Used by Web interface.
    """

    def __init__(self, config):
        super(GeneWeightsDb, self).__init__()
        self.config = config

        self.weights = OrderedDict()
        self._load()

    @staticmethod
    def load_gene_weight_from_file(filename, bins=150, xscale='linear',
                                   yscale='linear', desc=None, range=None):
        config = namedtuple(
            id=filename.split('.')[0],
            file=filename,
            desc=desc,
            bins=bins,
            xscale=xscale,
            yscale=yscale,
            range=range
        )
        return GeneWeight(config)

    def get_gene_weight_ids(self):
        return list(self.weights.keys())

    def get_gene_weight(self, weight_id):
        assert self[weight_id].df is not None
        return self[weight_id]

    def get_gene_weights(self):
        return [self.get_gene_weight(weight_id)
                for weight_id in self.weights]

    def _load(self):
        for weight_config in self.config.values():
            w = GeneWeight(weight_config)
            self.weights[weight_config.id] = w

    def __getitem__(self, weight_id):
        if weight_id not in self.weights:
            raise ValueError("unsupported gene weight {}".format(weight_id))

        res = self.weights[weight_id]
        if res.df is None:
            res.load_weights()
        return res

    def __contains__(self, weight_id):
        return weight_id in self.weights

    def __len__(self):
        return len(self.weights)
