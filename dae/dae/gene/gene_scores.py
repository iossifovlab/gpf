from __future__ import annotations

import os
import copy
import itertools
import logging
import textwrap
import json

from dataclasses import dataclass
from typing import Optional, Any, cast

import numpy as np
import pandas as pd
from jinja2 import Template

from dae.utils.dae_utils import join_line
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin, \
    ResourceStatistics

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import NumberHistogram, \
    NumberHistogramConfig
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class GeneScoreStatistics(ResourceStatistics):
    """
    Class for gene score statistics.

    Contains histograms mapped by score ID.
    """

    def __init__(
            self,
            resource_id: str,
            histograms: dict[str, NumberHistogram]) -> None:
        super().__init__(resource_id)
        self.score_histograms = histograms

    def get_histogram(self, score_id: str) -> Optional[NumberHistogram]:
        return self.score_histograms.get(score_id)

    @staticmethod
    def get_histogram_file(score_id: str) -> str:
        return f"histogram_{score_id}.yaml"

    @staticmethod
    def get_histogram_image_file(score_id: str) -> str:
        return f"histogram_{score_id}.png"

    @staticmethod
    def build_statistics(
        genomic_resource: GenomicResource
    ) -> ResourceStatistics:
        """Load gene score statistics."""
        histograms = {}
        config = genomic_resource.get_config()
        try:
            for score_config in config["scores"]:
                score_id = score_config["id"]
                hist_config = score_config.get("histogram")
                if hist_config is None:
                    print(f"Skipping {score_id}")
                    continue
                histogram_filepath = os.path.join(
                    GeneScoreStatistics.get_statistics_folder(),
                    GeneScoreStatistics.get_histogram_file(score_id)
                )
                with genomic_resource.open_raw_file(
                        histogram_filepath, mode="r") as infile:
                    histogram = NumberHistogram.deserialize(infile.read())
                    histograms[score_id] = histogram
        except FileNotFoundError:
            logger.exception(
                "Couldn't load statistics of %s", genomic_resource.resource_id
            )
            return GeneScoreStatistics(genomic_resource.resource_id, {})
        return GeneScoreStatistics(genomic_resource.resource_id, histograms)


class GeneScoreImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin
):
    """Class used to represent gene score resource implementations."""

    def __init__(self, resource: GenomicResource) -> None:
        super().__init__(resource)
        self.gene_score: GeneScore = build_gene_score_from_resource(
            resource
        )

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <hr>
            <h3>Gene scores file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>

            <h3>Gene score definitions:</h2>
            {% for score in data["scores"] %}
            <div class="score-definition">
            <p>Gene score ID: {{ score["id"] }}</p>
            <p>Description: {{ score["desc"] }}
            </div>
            {% endfor %}
            <h3>Histograms:</h2>
            {% for score in data["scores"] %}
            {% if score["histogram"] %}
            <div class="histogram">
            <h4>{{ score["id"] }}</h1>
            <img src="{{ data["statistics_dir"] }}/{{
                score["histogram"]["img_file"] }}"
            width="200px"
            alt={{ score["id"] }}
            title={{ score["id"] }}>
            </div>
            {% endif %}
            {% endfor %}
            {% endblock %}
        """))

    def get_statistics(self) -> ResourceStatistics:
        return self.gene_score.get_statistics()

    def _get_template_data(self) -> dict[str, Any]:
        data = copy.deepcopy(self.config)

        statistics = cast(GeneScoreStatistics, self.get_statistics())
        data["statistics_dir"] = statistics.get_statistics_folder()
        for score in data["scores"]:
            if "histogram" in score:
                score["histogram"]["img_file"] = \
                    statistics.get_histogram_image_file(
                        score["id"]
                )

        return data

    def get_info(self) -> str:
        return InfoImplementationMixin.get_info(self)

    def add_statistics_build_tasks(
            self, task_graph: TaskGraph, **kwargs: str) -> list[Task]:
        save_tasks = []
        for score_id, score_config in self.gene_score.score_configs.items():
            if score_config.get("histogram") is None:
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
                [create_task, self.resource, score_id],
                [create_task]
            )
            save_tasks.append(save_task)
        return save_tasks

    @staticmethod
    def _calc_histogram(
            resource: GenomicResource, score_id: str) -> NumberHistogram:
        score = build_gene_score_from_resource(resource)
        histogram_config = score.score_configs[score_id].get(
            "histogram"
        )
        if "view_range" not in histogram_config:
            histogram_config["view_range"] = {
                "min": score.get_min(score_id),
                "max": score.get_max(score_id)
            }

        config = NumberHistogramConfig.from_dict(histogram_config)

        # histogram_config = NumberHistogramConfig.from_dict(histogram_config)
        histogram = NumberHistogram(config)
        for value in score.get_values(score_id):
            histogram.add_value(value)
        return histogram

    @staticmethod
    def _save_histogram(
            histogram: NumberHistogram, resource: GenomicResource,
            score_id: str) -> NumberHistogram:
        proto = resource.proto
        with proto.open_raw_file(
            resource,
            f"{GeneScoreStatistics.get_statistics_folder()}"
            f"/{GeneScoreStatistics.get_histogram_file(score_id)}",
            mode="wt"
        ) as outfile:
            outfile.write(histogram.serialize())
        with proto.open_raw_file(
            resource,
            f"{GeneScoreStatistics.get_statistics_folder()}"
            f"/{GeneScoreStatistics.get_histogram_image_file(score_id)}",
            mode="wb"
        ) as outfile:
            histogram.plot(outfile, score_id)
        return histogram

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        manifest = self.resource.get_manifest()
        config = self.get_config()
        score_filename = config["filename"]
        return json.dumps({
            "score_config": [(
                score_id,
                self.gene_score.get_desc(score_id),
                self.gene_score.get_min(score_id),
                self.gene_score.get_max(score_id),
                self.gene_score.get_range(score_id),
                self.gene_score.get_x_scale(score_id),
                self.gene_score.get_y_scale(score_id)
            ) for score_id in self.gene_score.get_scores()],
            "score_file": manifest[score_filename].md5
        }, sort_keys=True, indent=2).encode()


class GeneScore(
    ResourceConfigValidationMixin
):
    """Class used to represent gene scores."""

    def __init__(self, resource: GenomicResource) -> None:
        super().__init__()

        if resource.get_type() != "gene_score":
            logger.error(
                "invalid resource type for gene score %s",
                resource.resource_id)
            raise ValueError(f"invalid resource type {resource.resource_id}")

        self.resource = resource
        self.config = self.validate_and_normalize_schema(
            resource.get_config(), resource
        )
        assert "filename" in self.config
        filename = self.config["filename"]

        with resource.open_raw_file(filename) as file:
            self.df = pd.read_csv(file)
        self.statistics: Optional[ResourceStatistics] = None

        if self.config.get("scores") is None:
            raise ValueError(f"missing scores config in {resource.get_id()}")
        self.score_configs = {
            score["id"]: score for score in
            self.config["scores"]
        }

        for score_id, config in self.score_configs.items():
            if config.get("histogram") is None:
                raise ValueError(
                    "Missing histogram config for "
                    f"{score_id} in {resource.get_id()}"
                )
        self.histograms: dict[str, Optional[NumberHistogram]] = {
            score["id"]: None for score in
            self.config["scores"]
        }

    def get_min(self, score_id: str) -> float:
        """Return minimal score value."""
        return float(self.df[score_id].min())

    def get_max(self, score_id: str) -> float:
        """Return maximal score value."""
        return float(self.df[score_id].max())

    def get_range(self, score_id: str) -> Optional[tuple[float]]:
        if score_id not in self.histograms:
            logger.warning("Score %s does not exist!", score_id)
            return None
        if self.histograms[score_id] is not None:
            return self.histograms[score_id].range  # type: ignore
        return None

    def get_desc(self, score_id: str) -> Optional[str]:
        if score_id not in self.score_configs:
            logger.warning("Score %s does not exist!", score_id)
            return None
        return self.score_configs.get(score_id).get("desc")  # type: ignore

    def get_values(self, score_id: str) -> list[float]:
        """Return a list of score values."""
        return cast(list[float], list(self.df[score_id].values))

    def get_x_scale(self, score_id: str) -> Optional[str]:
        """Return the scale type of the X axis."""
        if score_id not in self.score_configs:
            logger.warning("Score %s does not exist!", score_id)
            return None
        if "histogram" in self.score_configs[score_id]:
            config = self.score_configs[score_id]["histogram"]
            if config["type"] != "number":
                return None
            x_log_scale = config["x_log_scale"]
            return "log" if x_log_scale else "linear"
        return "linear"

    def get_y_scale(self, score_id: str) -> Optional[str]:
        """Return the scale type of the Y axis."""
        if score_id not in self.score_configs:
            logger.warning("Score %s does not exist!", score_id)
            return None
        if "histogram" in self.score_configs[score_id]:
            config = self.score_configs[score_id]["histogram"]
            y_log_scale = config["y_log_scale"]
            return "log" if y_log_scale else "linear"
        return "linear"

    def get_genes(
            self, score_id: str,
            score_min: Optional[float] = None,
            score_max: Optional[float] = None) -> set[str]:
        """Return set of genes for a score between a min and max value."""
        score_value_df = self.get_score_df(score_id)
        df = score_value_df[score_id]
        if score_min is None or score_min < df.min() or score_min > df.max():
            score_min = float("-inf")
        if score_max is None or score_max < df.min() or score_max > df.max():
            score_max = float("inf")

        index = np.logical_and(
            df.values >= score_min, df.values < score_max)  # type: ignore
        index = np.logical_and(index, df.notnull())
        genes = score_value_df[index].gene
        return set(genes.values)

    def get_scores(self) -> list[str]:
        return list(self.score_configs.keys())

    def _to_dict(self, score_id: str) -> dict[str, Any]:
        """Return dictionary of all defined scores keyed by gene symbol."""
        return cast(
            dict[str, Any],
            self.get_score_df(
                score_id).set_index("gene")[score_id].to_dict())

    def get_gene_value(
            self, score_id: str, gene_symbol: str) -> Optional[float]:
        """Return the value for a given gene symbol."""
        symbol_values = self._to_dict(score_id)
        return symbol_values.get(gene_symbol)

    def _to_list(self, df: Optional[pd.DataFrame] = None) -> list[str]:
        if df is None:
            df = self.df
        columns = df.applymap(str).columns.tolist()
        values = df.applymap(str).values.tolist()

        return cast(
            list[str],
            list(itertools.chain([columns], values)))

    def to_tsv(self, score_id: Optional[str] = None) -> list[str]:
        """Return a TSV version of the gene score data."""
        df = None
        if score_id is not None:
            df = self.get_score_df(score_id)
        return list(map(join_line, self._to_list(df)))

    def get_score_df(self, score_id: str) -> pd.DataFrame:
        return self.df[["gene", score_id]].dropna()

    def get_statistics(self) -> ResourceStatistics:
        if self.statistics is None:
            self.statistics = GeneScoreStatistics.build_statistics(
                self.resource
            )
        return self.statistics

    @property
    def files(self) -> set[str]:
        files = set()
        files.add(self.resource.get_config().get("filename"))
        return files

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "scores": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "desc": {"type": "string"},
                    "histogram": {"type": "dict", "schema": {
                        "type": {"type": "string"},
                        "number_of_bins": {
                            "type": "number",
                            "dependencies": {"type": "number"}
                        },
                        "view_range": {"type": "dict", "schema": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        }, "dependencies": {"type": "number"}},
                        "x_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": "number"}
                        },
                        "y_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": ["number", "categorical"]}
                        },
                        "x_min_log": {
                            "type": "number",
                            "dependencies": {"type": ["number", "categorical"]}
                        },
                        "value_order": {
                            "type": "list", "schema": {"type": "string"},
                            "dependencies": {"type": "categorical"}
                        },
                        "reason": {
                            "type": "string",
                            "dependencies": {"type": "null"}
                        }
                    }},
                }
            }},
        }

    def get_histogram(self, score_id: str) -> Optional[NumberHistogram]:
        if self.histograms[score_id] is None:
            statistics = cast(GeneScoreStatistics, self.get_statistics())
            self.histograms[score_id] = statistics.get_histogram(score_id)

        return self.histograms[score_id]

    @staticmethod
    def get_histogram_file(score_id: str) -> str:
        return GeneScoreStatistics.get_histogram_file(score_id)

    @staticmethod
    def get_histogram_image_file(score_id: str) -> str:
        return GeneScoreStatistics.get_histogram_image_file(score_id)


@dataclass
class ScoreDesc:
    resource_id: str
    score_id: str
    number_hist: Optional[NumberHistogram]
    description: Optional[str]


class GeneScoresDb:
    """
    Helper class used to load all defined gene scores.

    Used by Web interface.
    """

    def __init__(self, gene_scores: list[GeneScore]):
        super().__init__()
        self.score_descs = {}
        self.gene_scores = {}
        for gene_score in gene_scores:
            self.gene_scores[gene_score.resource.get_id()] = gene_score
            for score_desc in GeneScoresDb._build_descs_from_score(gene_score):
                self.score_descs[score_desc.score_id] = score_desc

    @staticmethod
    def _build_descs_from_score(gene_score: GeneScore) -> list[ScoreDesc]:
        result = []
        for score_id in gene_score.get_scores():
            result.append(ScoreDesc(
                resource_id=gene_score.resource.get_id(),
                score_id=score_id,
                number_hist=gene_score.get_histogram(score_id),
                description=gene_score.get_desc(score_id)
            ))
        return result

    def get_score_ids(self) -> list[str]:
        """Return a list of the IDs of all the gene scores contained."""
        return sorted(list(self.score_descs.keys()))

    def get_gene_score_ids(self) -> list[str]:
        """Return a list of the IDs of all the gene scores contained."""
        return sorted(list(self.gene_scores.keys()))

    def get_gene_scores(self) -> list[GeneScore]:
        """Return a list of all the gene scores contained in the DB."""
        return list(self.gene_scores.values())

    def get_scores(self) -> list[ScoreDesc]:
        return list(self.score_descs.values())

    def get_gene_score(self, score_id: str) -> Optional[GeneScore]:
        """Return a given gene score."""
        if score_id not in self.gene_scores:
            return None
        assert self.gene_scores[score_id].df is not None
        return self.gene_scores[score_id]

    def get_score_desc(self, score_id: str) -> Optional[ScoreDesc]:
        if score_id not in self.score_descs:
            return None
        return self.score_descs[score_id]

    def __getitem__(self, score_id: str) -> ScoreDesc:
        if score_id not in self.score_descs:
            raise ValueError(f"score {score_id} not found")

        res = self.score_descs[score_id]
        return res

    def __contains__(self, score_id: str) -> bool:
        return score_id in self.score_descs

    def __len__(self) -> int:
        return len(self.score_descs)


def build_gene_score_from_resource(resource: GenomicResource) -> GeneScore:
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneScore(resource)


def build_gene_score_implementation_from_resource(
        resource: GenomicResource) -> GenomicResourceImplementation:
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneScoreImplementation(resource)
