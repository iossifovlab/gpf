import itertools
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

from dae.gene.gene_sets_db import cached
from dae.utils.dae_utils import join_line
from dae.genomic_resources.aggregators import build_aggregator

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import Histogram


class GeneScore:
    """
    Represents gene scores.

    Loads a CSV file with gene scores by gene score id as described
    in resource config.

    Gene Score resource configuration format:
    type: gene_score
    gene_scores:
      - id: (gene score id)
        filename: (filename to gene score)
        desc: (gene score description)
    histograms:
      - score: (gene score id)
        bins: (number of bins)
        x_scale: linear/log
        y_scale: linear/log
    meta: (gene score metadata)
    """

    DEFAULT_AGGREGATOR_TYPE = "dict"

    def __init__(self, score_id, file, desc, histogram_config, meta=None):
        self.histogram_config = histogram_config

        self.score_id = score_id
        self.df = None
        self._dict = None

        self.genomic_values_col = "gene"

        self.desc = desc
        self.file = file

        self.meta = meta

        self._load_data()
        self.df.dropna(inplace=True)

        if "min" not in histogram_config:
            histogram_config["min"] = self.min()
        if "max" not in histogram_config:
            histogram_config["max"] = self.max()
        self.histogram = Histogram.from_config(histogram_config)
        self.histogram.set_bins_bars(self.values())

        self.histogram_bins = self.histogram.bins
        self.histogram_bars = self.histogram.bars

    @property
    def x_scale(self):
        """Return the scale type of the X axis."""
        return self.histogram.x_scale

    @property
    def y_scale(self):
        """Returns the scale type of the Y axis."""
        return self.histogram.y_scale

    def _load_data(self):
        assert self.file is not None

        df = pd.read_csv(self.file)
        assert self.score_id in df.columns, "{} not found in {}".format(
            self.score_id, df.columns
        )
        self.df = df[[self.genomic_values_col, self.score_id]].copy()
        return self.df

    @staticmethod
    def load_gene_scores_from_resource(
            resource: Optional[GenomicResource]):
        """Create and return all of the gene scores described in a resource."""
        assert resource is not None
        assert resource.get_type() == "gene_score", "Invalid resource type"

        config = resource.get_config()
        meta = getattr(config, "meta", None)
        scores = []
        for gs_config in config["gene_scores"]:
            gene_score_id = gs_config["id"]
            file = resource.open_raw_file(config["filename"])
            desc = gs_config["desc"]
            histogram_config = None
            for hist_config in config["histograms"]:
                if hist_config["score"] == gene_score_id:
                    histogram_config = hist_config
                    break
            assert histogram_config is not None
            gs = GeneScore(gene_score_id, file, desc, histogram_config, meta)
            scores.append(gs)

        return scores

    def values(self):
        """Return a list of score values."""
        return self.df[self.score_id].values

    def get_gene_value(self, gene_symbol):
        """Return the value for a given gene symbol."""
        symbol_values = self._to_dict()
        return symbol_values[gene_symbol]

    def aggregate_gene_values(self, gene_symbols, aggregator_type=None):
        if aggregator_type is None:
            aggregator_type = self.DEFAULT_AGGREGATOR_TYPE
        aggregator = build_aggregator(aggregator_type)

        for gs in gene_symbols:
            aggregator.add(self.get_gene_value(gs), key=gs)

        return aggregator.get_final()

    @cached
    def _to_dict(self):
        """Return dictionary of all defined scores keyed by gene symbol."""
        if self._dict is None:
            self._dict = self.df.set_index("gene")[self.score_id].to_dict()
        return self._dict

    @cached
    def _to_list(self):
        columns = self.df.applymap(str).columns.tolist()
        values = self.df.applymap(str).values.tolist()

        return itertools.chain([columns], values)

    @cached
    def to_tsv(self):
        """Return a TSV version of the gene score data."""
        return map(join_line, self._to_list())

    @cached
    def min(self):
        """Return minimal score value."""
        return self.df[self.score_id].min()

    @cached
    def max(self):
        """Return maximal score value."""
        return self.df[self.score_id].max()

    def get_genes(self, wmin=None, wmax=None):
        """
        Return a set of genes which scores are between `wmin` and `wmax`.

        `wmin` -- the lower bound of scores. If not specified or `None`
        works without lower bound.

        `wmax` -- the upper bound of scores. If not specified or `None`
        works without upper bound.
        """
        df = self.df[self.score_id]
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
        super().__init__()
        self.scores = OrderedDict()
        for score in gene_scores:
            self.scores[score.score_id] = score

    @cached
    def get_gene_score_ids(self):
        """Return a list of the IDs of all the gene scores contained."""
        return list(self.scores.keys())

    @cached
    def get_gene_scores(self):
        """Return a list of all the gene scores contained in the DB."""
        return [self.get_gene_score(score_id) for score_id in self.scores]

    def get_gene_score(self, score_id):
        """Return a given gene score."""
        assert self[score_id].df is not None
        return self[score_id]

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise ValueError(f"unsupported gene score {score_id}")

        res = self.scores[score_id]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_id):
        return score_id in self.scores

    def __len__(self):
        return len(self.scores)
