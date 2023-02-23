from __future__ import annotations
import copy
import itertools
import logging
import textwrap
import hashlib
import json
from typing import Optional, List

import numpy as np
import pandas as pd
from jinja2 import Template
from cerberus import Validator

from dae.utils.dae_utils import join_line
from dae.genomic_resources.aggregators import build_aggregator
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import Histogram
from dae.task_graph.graph import Task

logger = logging.getLogger(__name__)


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

    def __init__(
        self, score_id, file, desc, histogram_config, meta=None, histogram=None
    ):
        self.histogram_config = histogram_config

        self.score_id = score_id
        self.genomic_values_col = "gene"

        self.desc = desc
        self.file = file

        self.meta = meta

        self.df = self._load_data()
        self.df.dropna(inplace=True)

        self.histogram = histogram
        self.histogram_bins = None
        self.histogram_bars = None

        if histogram is not None:
            self.histogram_bins = self.histogram.bins
            self.histogram_bars = self.histogram.bars

    @property
    def x_scale(self):
        """Return the scale type of the X axis."""
        if self.histogram is not None:
            return self.histogram.x_scale
        return self.histogram_config.get("x_scale")

    @property
    def y_scale(self):
        """Return the scale type of the Y axis."""
        if self.histogram is not None:
            return self.histogram.y_scale
        return self.histogram_config.get("y_scale")

    @property
    def range(self):
        if self.histogram is not None:
            return self.histogram.range
        return None

    def _load_data(self):
        assert self.file is not None

        df = pd.read_csv(self.file)
        assert self.score_id in df.columns, \
            f"{self.score_id} not found in {df.columns}"
        return df[[self.genomic_values_col, self.score_id]].copy()

    @staticmethod
    def load_gene_scores_from_resource(
            resource: Optional[GenomicResource]) -> List[GeneScore]:
        """Create and return all of the gene scores described in a resource."""
        assert resource is not None
        if resource.get_type() != "gene_score":
            logger.error(
                "invalid resource type for gene score %s",
                resource.resource_id)
            raise ValueError(f"invalid resource type {resource.resource_id}")
        logger.info("processing gene score %s", resource.resource_id)

        config = resource.get_config()
        if config.get("gene_scores") is None:
            raise ValueError(
                f"missing gene_scores config {resource.resource_id}")
        if config.get("histograms") is None:
            raise ValueError(
                f"missing histograms config {resource.resource_id}")

        scores = []
        for gs_config in config["gene_scores"]:
            gene_score = GeneScore._load_gene_score(resource, gs_config)
            scores.append(gene_score)

        return scores

    @staticmethod
    def load_gene_score_from_resource(
        resource: GenomicResource, score_id: str
    ):
        """Create and return specific gene score in a resource."""
        if resource.get_type() != "gene_score":
            logger.error(
                "invalid resource type for gene score %s",
                resource.resource_id)
            raise ValueError(f"invalid resource type {resource.resource_id}")

        config = resource.get_config()
        for gs_config in config["gene_scores"]:
            if gs_config["id"] == score_id:
                return GeneScore._load_gene_score(resource, gs_config)

        return None

    @staticmethod
    def _load_gene_score(resource, gs_config):
        proto = resource.proto
        resource_config = resource.get_config()
        gene_score_id = gs_config["id"]
        file = resource.open_raw_file(resource_config["filename"])
        desc = gs_config["desc"]
        histogram_config = None
        for hist_config in resource_config["histograms"]:
            if hist_config["score"] == gene_score_id:
                histogram_config = hist_config
                break
        if histogram_config is None:
            raise ValueError(
                f"missing histogram config for score {gene_score_id} in "
                f"resource {resource.resource_id}"
            )
        histogram_filename = (
            f"{GeneScoreCollection.STATISTICS_FOLDER}"
            f"/histogram_{gene_score_id}.yaml"
        )
        histogram = None
        if proto.file_exists(resource, histogram_filename):
            with proto.open_raw_file(
                resource,
                histogram_filename,
                mode="rt"
            ) as infile:
                histogram = Histogram.deserialize(infile.read())

        meta = resource_config.get("meta")

        return GeneScore(
            gene_score_id, file, desc, histogram_config,
            meta=meta, histogram=histogram)

    def values(self):
        """Return a list of score values."""
        return self.df[self.score_id].values

    def get_gene_value(self, gene_symbol):
        """Return the value for a given gene symbol."""
        symbol_values = self._to_dict()
        return symbol_values[gene_symbol]

    def aggregate_gene_values(self, gene_symbols, aggregator_type=None):
        """Aggregate values for given symbols with given aggregator type."""
        if aggregator_type is None:
            aggregator_type = self.DEFAULT_AGGREGATOR_TYPE
        aggregator = build_aggregator(aggregator_type)

        for symbol in gene_symbols:
            aggregator.add(self.get_gene_value(symbol), key=symbol)

        return aggregator.get_final()

    def _to_dict(self):
        """Return dictionary of all defined scores keyed by gene symbol."""
        return self.df.set_index("gene")[self.score_id].to_dict()

    def _to_list(self):
        columns = self.df.applymap(str).columns.tolist()
        values = self.df.applymap(str).values.tolist()

        return itertools.chain([columns], values)

    def to_tsv(self):
        """Return a TSV version of the gene score data."""
        return map(join_line, self._to_list())

    def min(self):
        """Return minimal score value."""
        return self.df[self.score_id].min().item()

    def max(self):
        """Return maximal score value."""
        return self.df[self.score_id].max().item()

    def get_genes(self, score_min=None, score_max=None):
        """
        Return genes which scores are between `score_min` and `score_max`.

        `score_min` -- the lower bound of scores. If not specified or `None`
        works without lower bound.

        `score_max` -- the upper bound of scores. If not specified or `None`
        works without upper bound.
        """
        df = self.df[self.score_id]
        df.dropna(inplace=True)

        if score_min is None or score_min < df.min() or score_min > df.max():
            score_min = float("-inf")
        if score_max is None or score_max < df.min() or score_max > df.max():
            score_max = float("inf")

        index = np.logical_and(df.values >= score_min, df.values < score_max)
        genes = self.df[index].gene
        return set(genes.values)


class GeneScoreCollection(
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin
):
    """Class used to represent all gene scores in a resource."""

    config_validator = Validator

    def __init__(self, resource):
        super().__init__(resource)
        self.config = self.validate_and_normalize_schema(
            self.config, resource
        )
        self.scores = {
            score.score_id: score for score in
            GeneScore.load_gene_scores_from_resource(self.resource)
        }

    def get_template(self):
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <hr>
            <h3>Gene scores file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>

            <h3>Gene score definitions:</h2>
            {% for score in data["gene_scores"] %}
            <div class="score-definition">
            <p>Gene score ID: {{ score["id"] }}</p>
            <p>Description: {{ score["desc"] }}
            </div>
            <h3>Histograms:</h2>
            {% for hist in data["histograms"] %}
            <div class="histogram">
            <h4>{{ hist["score"] }}</h1>
            <img src="histograms/{{ hist["score"] }}.png"
            alt={{ hist["score"] }}
            title={{ hist["score"] }}>
            </div>
            {% endfor %}
            {% endfor %}
            {% endblock %}
        """))

    def _get_template_data(self):
        data = copy.deepcopy(self.config)
        return data

    @property
    def files(self):
        raise NotImplementedError

    @staticmethod
    def get_schema():
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "gene_scores": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "desc": {"type": "string"},
                }
            }},
            "histograms": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "score": {"type": "string"},
                    "bins": {"type": "integer"},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                    "x_min_log": {"type": "number"},
                    "x_scale": {"type": "string"},
                    "y_scale": {"type": "string"},
                }
            }},
        }

    def get_info(self):
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self):
        return "placeholder"

    def calc_statistics_hash(self) -> bytes:
        manifest = self.resource.get_manifest()
        score_filename = self.get_config()["filename"]
        return hashlib.md5(json.dumps({
            "config": manifest["genomic_resource.yaml"].md5,
            "score_file": manifest[score_filename].md5
        }, sort_keys=True).encode()).digest()

    def add_statistics_build_tasks(self, task_graph, **kwargs) -> List[Task]:
        save_tasks = []
        for score_id, score in self.scores.items():
            if score.histogram_config is None:
                logger.warning(
                    "Gene score %s in %s has no histogram config!",
                    score_id, self.resource.resource_id
                )
                continue
            create_task = task_graph.create_task(
                f"{self.resource.resource_id}_{score_id}_calc_histogram",
                self._calc_histogram,
                [self.resource, score_id],
                []
            )
            save_task = task_graph.create_task(
                f"{self.resource.resource_id}_{score_id}_save_histogram",
                self._save_histogram,
                [create_task, self.resource],
                [create_task]
            )
            save_tasks.append(save_task)
        return save_tasks

    @staticmethod
    def _calc_histogram(resource, score_id):
        score = GeneScore.load_gene_score_from_resource(resource, score_id)
        histogram_config = score.histogram_config
        if "min" not in histogram_config:
            histogram_config["min"] = score.min()
        if "max" not in histogram_config:
            histogram_config["max"] = score.max()
        histogram = Histogram(score.histogram_config)
        for value in score.values():
            histogram.add_value(value)
        return histogram

    @staticmethod
    def _save_histogram(histogram, resource):
        proto = resource.proto
        score_id = histogram.score_id
        with proto.open_raw_file(
            resource,
            f"{GeneScoreCollection.STATISTICS_FOLDER}"
            f"/histogram_{score_id}.yaml",
            mode="wt"
        ) as outfile:
            outfile.write(histogram.serialize())
        return histogram


class GeneScoresDb:
    """
    Helper class used to load all defined gene scores.

    Used by Web interface.
    """

    def __init__(self, collections):
        super().__init__()
        self.scores = {}
        for collection in collections:
            for score_id, score in collection.scores.items():
                self.scores[score_id] = score

    def get_gene_score_ids(self):
        """Return a list of the IDs of all the gene scores contained."""
        return sorted(list(self.scores.keys()))

    def get_gene_scores(self):
        """Return a list of all the gene scores contained in the DB."""
        return [self.get_gene_score(score_id) for score_id in self.scores]

    def get_gene_score(self, score_id):
        """Return a given gene score."""
        if score_id not in self.scores:
            return None
        assert self.scores[score_id].df is not None
        return self.scores[score_id]

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise ValueError(f"gene score {score_id} not found")

        res = self.scores[score_id]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_id):
        return score_id in self.scores

    def __len__(self):
        return len(self.scores)


def build_gene_score_collection_from_resource(resource: GenomicResource):
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneScoreCollection(resource)
