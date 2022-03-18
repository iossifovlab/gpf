import itertools
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

from dae.gene.gene_sets_db import cached
from dae.utils.dae_utils import join_line

from dae.genomic_resources import GenomicResource


class GeneScore:
    """
    Represents gene scores.

    Loads a CSV file with gene scores by gene score id as described
    in resource config.

    Gene Score resource configuration format:
    type: gene_score
    id: (gene score id)
    filename: (filename to gene score)
    desc: (gene score description)
    histogram:
      bins: (number of bins)
      xscale: linear/log
      yscale: linear/log
    meta: (gene score metadata)
    """

    def __init__(self, score_id, file, desc, histogram_config, meta=None):
        self.histogram_config = histogram_config

        self.id = score_id
        self.df = None
        self._dict = None

        self.genomic_values_col = "gene"

        self.desc = desc
        self.bins = self.histogram_config["bins"]
        self.xscale = self.histogram_config["xscale"]
        self.yscale = self.histogram_config["yscale"]
        self.file = file
        self.range = getattr(self.histogram_config, "range", None)

        self.meta = meta

        self._load_data()
        self.df.dropna(inplace=True)

        self.histogram_bins, self.histogram_bars = self._bins_bars()

    def _load_data(self):
        assert self.file is not None

        df = pd.read_csv(self.file)
        assert self.id in df.columns, "{} not found in {}".format(
            self.id, df.columns
        )
        self.df = df[[self.genomic_values_col, self.id]].copy()
        return self.df

    @staticmethod
    def load_gene_score_from_resource(
            resource: Optional[GenomicResource]):
        assert resource is not None
        print(resource.get_type())
        assert resource.get_type() == "gene_score", "Invalid resource type"

        config = resource.get_config()
        gene_score_id = config["id"]
        file = resource.open_raw_file(config["filename"])
        histogram_config = config["histogram"]
        desc = config["desc"]
        meta = getattr(config, "meta", None)
        return GeneScore(gene_score_id, file, desc, histogram_config, meta)

    def values(self):
        return self.df[self.id].values

    def _bins_bars(self):
        step = 1.0 * (self.max() - self.min()) / (self.bins - 1)
        dec = -np.log10(step)
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

            bins_in = [0] + list(
                np.logspace(bleft, np.log10(bright), self.bins)
            )
        else:
            bins_in = self.bins

        bars, bins = np.histogram(
            list(self.values()), bins_in, range=[bleft, bright]
        )

        return (bins, bars)

    def get_gene_value(self, gene_symbol):
        symbol_values = self._to_dict()
        return symbol_values[gene_symbol]

    @cached
    def _to_dict(self):
        """
        Returns dictionary of all defined scores keyed by gene symbol.
        """
        if self._dict is None:
            self._dict = self.df.set_index("gene")[self.id].to_dict()
        return self._dict

    @cached
    def _to_list(self):
        columns = self.df.applymap(str).columns.tolist()
        values = self.df.applymap(str).values.tolist()

        return itertools.chain([columns], values)

    @cached
    def to_tsv(self):
        return map(join_line, self._to_list())

    @cached
    def min(self):
        """
        Returns minimal score value.
        """
        return self.df[self.id].min()

    @cached
    def max(self):
        """
        Returns maximal score value.
        """
        return self.df[self.id].max()

    def get_genes(self, wmin=None, wmax=None):
        """
        Returns a set of genes which scores are between `wmin` and `wmax`.

        `wmin` -- the lower bound of scores. If not specified or `None`
        works without lower bound.

        `wmax` -- the upper bound of scores. If not specified or `None`
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


class GeneScoresDb:
    """
    Helper class used to load all defined gene scores.

    Used by Web interface.
    """

    def __init__(self, gene_scores):
        super(GeneScoresDb, self).__init__()
        self.scores = OrderedDict()
        for score in gene_scores:
            self.scores[score.id] = score

    @cached
    def get_gene_score_ids(self):
        return list(self.scores.keys())

    @cached
    def get_gene_scores(self):
        return [self.get_gene_score(score_id) for score_id in self.scores]

    def get_gene_score(self, score_id):
        assert self[score_id].df is not None
        return self[score_id]

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise ValueError("unsupported gene score {}".format(score_id))

        res = self.scores[score_id]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_id):
        return score_id in self.scores

    def __len__(self):
        return len(self.scores)
