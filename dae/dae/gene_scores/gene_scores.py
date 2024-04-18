from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional, cast
from urllib.parse import quote

import numpy as np
import pandas as pd
from jinja2 import Template

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import (
    NumberHistogram,
    NumberHistogramConfig,
    build_histogram_config,
    load_histogram,
)
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)
from dae.genomic_scores.scores import SCORE_HISTOGRAM
from dae.utils.dae_utils import join_line

logger = logging.getLogger(__name__)


@dataclass
class ScoreDef:
    """Class used to represent a gene score definition."""

    score_id: str
    name: str
    desc: str

    hist_conf: Optional[NumberHistogramConfig]
    small_values_desc: Optional[str]
    large_values_desc: Optional[str]


class GeneScore(
    ResourceConfigValidationMixin,
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
        config = resource.get_config()
        if config is None:
            raise ValueError(
                f"genomic resource {resource.resource_id} not configured")
        self.config = self.validate_and_normalize_schema(config, resource)
        assert "filename" in self.config
        self.filename = self.config["filename"]

        compression = False
        if self.filename.endswith(".gz"):
            compression = True

        with resource.open_raw_file(
                self.filename, compression=compression) as file:
            self.df = pd.read_csv(file, sep=self.config["separator"])

        if self.config.get("scores") is None:
            raise ValueError(f"missing scores config in {resource.get_id()}")

        self.score_definitions: dict[str, ScoreDef] = {}

        for score_conf in self.config["scores"]:
            score_id = score_conf["id"]
            score_name = score_conf.get("name", score_id)
            hist_conf = build_histogram_config(score_conf)

            if not isinstance(hist_conf, NumberHistogramConfig):
                raise ValueError(
                    f"Missing histogram config for {score_id} in "
                    f"{self.resource.resource_id}")

            if not hist_conf.has_view_range():
                min_value = self.get_min(score_id)
                max_value = self.get_max(score_id)
                hist_conf.view_range = (min_value, max_value)

            self.score_definitions[score_conf["id"]] = ScoreDef(
                score_id,
                score_name,
                score_conf.get("desc", ""),
                hist_conf,
                score_conf.get("small_values_desc"),
                score_conf.get("large_values_desc"),
            )

    def get_min(self, score_id: str) -> float:
        """Return minimal score value."""
        return float(self.df[score_id].min())

    def get_max(self, score_id: str) -> float:
        """Return maximal score value."""
        return float(self.df[score_id].max())

    def get_values(self, score_id: str) -> list[float]:
        """Return a list of score values."""
        return cast(list[float], list(self.df[score_id].values))

    def _get_hist_conf(self, score_id: str) -> Optional[NumberHistogramConfig]:
        if score_id not in self.score_definitions:
            logger.warning("Score %s does not exist!", score_id)
            raise ValueError(
                f"unexpected score_id {score_id} for gene score "
                f"{self.resource.resource_id}")
        hist_conf = self.score_definitions[score_id].hist_conf
        if hist_conf is None:
            logger.warning(
                "histogram not configured for %s for gene score %s",
                score_id, self.resource.resource_id)
            return None
        if not isinstance(hist_conf, NumberHistogramConfig):
            return None
        return hist_conf

    def get_x_scale(self, score_id: str) -> Optional[str]:
        """Return the scale type of the X axis."""
        hist_conf = self._get_hist_conf(score_id)
        if hist_conf is None:
            return None
        if hist_conf.x_log_scale:
            return "log"
        return "linear"

    def get_y_scale(self, score_id: str) -> Optional[str]:
        """Return the scale type of the Y axis."""
        hist_conf = self._get_hist_conf(score_id)
        if hist_conf is None:
            return None
        if hist_conf.y_log_scale:
            return "log"
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
        return self.get_all_scores()

    @lru_cache(maxsize=64)
    def get_all_scores(self) -> list[str]:
        return list(self.score_definitions.keys())

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
        return list(map(join_line, self._to_list(df)))  # type: ignore

    def get_score_df(self, score_id: str) -> pd.DataFrame:
        return self.df[["gene", score_id]].dropna()

    @property
    def files(self) -> set[str]:
        return {self.config["filename"]}

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "separator": {"type": "string", "default": ","},
            "scores": {"type": "list", "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "desc": {"type": "string"},
                    "large_values_desc": {"type": "string"},
                    "small_values_desc": {"type": "string"},
                    "number_hist": {"type": "dict", "schema": {
                        "number_of_bins": {
                            "type": "number",
                        },
                        "view_range": {"type": "dict", "schema": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        }},
                        "x_log_scale": {
                            "type": "boolean",
                        },
                        "y_log_scale": {
                            "type": "boolean",
                        },
                        "x_min_log": {
                            "type": "number",
                        },
                    }},
                    "histogram": {"type": "dict", "schema": {
                        "type": {"type": "string"},
                        "number_of_bins": {
                            "type": "number",
                            "dependencies": {"type": "number"},
                        },
                        "view_range": {"type": "dict", "schema": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        }, "dependencies": {"type": "number"}},
                        "x_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": "number"},
                        },
                        "y_log_scale": {
                            "type": "boolean",
                            "dependencies": {"type": ["number", "categorical"]},
                        },
                        "x_min_log": {
                            "type": "number",
                            "dependencies": {"type": ["number", "categorical"]},
                        },
                        "value_order": {
                            "type": "list", "schema": {"type": "string"},
                            "dependencies": {"type": "categorical"},
                        },
                        "reason": {
                            "type": "string",
                            "dependencies": {"type": "null"},
                        },
                    }},
                },
            }},
        }

    @lru_cache(maxsize=64)
    def get_number_range(
            self, score_id: str) -> Optional[tuple[float, float]]:
        """Return the value range for a number score."""
        if score_id not in self.get_all_scores():
            raise ValueError(
                f"unknown score {score_id}; "
                f"available scores are {self.get_all_scores()}")
        hist = self.get_score_histogram(score_id)
        if isinstance(hist, NumberHistogram):
            return (hist.min_value, hist.max_value)
        return None

    def get_histogram_filename(self, score_id: str) -> str:
        return f"statistics/histogram_{score_id}.yaml"

    @lru_cache(maxsize=64)
    def get_score_histogram(self, score_id: str) -> NumberHistogram:
        """Return defined histogram for a score."""
        if score_id not in self.score_definitions:
            raise ValueError(
                f"unexpected gene score ID {score_id}; available scores are: "
                f"{self.get_all_scores()}")

        hist_filename = self.get_histogram_filename(score_id)
        hist = load_histogram(self.resource, hist_filename)
        return cast(NumberHistogram, hist)

    def get_histogram_image_filename(self, score_id: str) -> str:
        return f"statistics/histogram_{score_id}.png"

    def get_histogram_image_url(self, score_id: str) -> Optional[str]:
        return f"{self.resource.get_url()}/" \
            f"{quote(self.get_histogram_image_filename(score_id))}"


@dataclass
class ScoreDesc:
    """Class used to represent a score description."""

    resource_id: str
    score_id: str
    name: str
    hist: NumberHistogram
    description: str
    help: str
    small_values_desc: Optional[str]
    large_values_desc: Optional[str]


GENE_SCORE_HELP = """

<div class="score-description">

## {{ data.name }}

{{ data.description}}

{{ data.resource_summary }}

{{ data.histogram }}

Genomic resource:
<a href={{data.resource_url}} target="_blank">{{ data.resource_id }}</a>

</div>

"""


def _build_gene_score_help(
    score_def: ScoreDef,
    gene_score: GeneScore,
) -> str:
    score_id = score_def.score_id
    hist_url = gene_score.get_histogram_image_url(score_id)
    assert score_def is not None

    histogram = Template(SCORE_HISTOGRAM).render(
        hist_url=hist_url,
        score_def=score_def,
    )

    data = {
        "name": score_def.score_id,
        "description": score_def.desc,
        "resource_id": gene_score.resource.resource_id,
        "resource_summary": gene_score.resource.get_summary(),
        "resource_url": f"{gene_score.resource.get_url()}/index.html",
        "histogram": histogram,
    }
    template = Template(GENE_SCORE_HELP)
    return template.render(data=data)


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
    def _build_descs_from_score(
        gene_score: GeneScore,
    ) -> list[ScoreDesc]:
        result = []
        for score_id, score_def in gene_score.score_definitions.items():
            help_doc = _build_gene_score_help(score_def, gene_score)
            result.append(ScoreDesc(
                resource_id=gene_score.resource.resource_id,
                score_id=score_id,
                name=score_def.name,
                hist=gene_score.get_score_histogram(score_id),
                description=score_def.desc,
                help=help_doc,
                small_values_desc=score_def.small_values_desc,
                large_values_desc=score_def.large_values_desc,
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
