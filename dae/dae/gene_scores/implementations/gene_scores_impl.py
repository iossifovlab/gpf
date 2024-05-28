from __future__ import annotations

import json
import logging
import textwrap
from dataclasses import asdict
from typing import Any

from jinja2 import Template

from dae.gene_scores.gene_scores import (
    GeneScore,
    build_gene_score_from_resource,
)
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import (
    NullHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class GeneScoreImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Class used to represent gene score resource implementations."""

    def __init__(self, resource: GenomicResource) -> None:
        super().__init__(resource)
        self.gene_score: GeneScore = build_gene_score_from_resource(
            resource,
        )

    def get_template(self) -> Template:
        return Template(GENE_SCORES_TEMPLATE)

    def _get_template_data(self) -> dict[str, Any]:
        data = {}
        data["gene_score"] = self.gene_score
        return data

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def add_statistics_build_tasks(
            self, task_graph: TaskGraph, **kwargs: str) -> list[Task]:
        save_tasks = []
        for score_id, score_def in self.gene_score.score_definitions.items():
            hist_conf = score_def.hist_conf
            if hist_conf is None or isinstance(hist_conf, NullHistogramConfig):
                logger.warning(
                    "Gene score %s in %s has no histogram config!",
                    score_id, self.resource.resource_id,
                )
                continue
            create_task = task_graph.create_task(
                f"{self.resource.resource_id}_{score_id}_calc_histogram",
                self._calc_histogram,
                [self.resource, score_id],
                [],
            )
            save_task = task_graph.create_task(
                f"{self.resource.resource_id}_{score_id}_save_histogram",
                self._save_histogram,
                [create_task, self.resource, score_id],
                [create_task],
            )
            save_tasks.append(save_task)
        return save_tasks

    @staticmethod
    def _calc_histogram(
            resource: GenomicResource, score_id: str) -> NumberHistogram:
        score = build_gene_score_from_resource(resource)
        hist_conf = score.score_definitions[score_id].hist_conf
        assert isinstance(hist_conf, NumberHistogramConfig)

        histogram = NumberHistogram(hist_conf)
        for value in score.get_values(score_id):
            histogram.add_value(value)
        return histogram

    @staticmethod
    def _save_histogram(
            histogram: NumberHistogram, resource: GenomicResource,
            score_id: str) -> NumberHistogram:
        proto = resource.proto
        gene_score = build_gene_score_from_resource(resource)

        with proto.open_raw_file(
            resource,
            gene_score.get_histogram_filename(score_id),
            mode="wt",
        ) as outfile:
            outfile.write(histogram.serialize())
        with proto.open_raw_file(
            resource,
            gene_score.get_histogram_image_filename(score_id),
            mode="wb",
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
            "score_config": [
                {
                    "id": score_def.score_id,
                    "hist_conf": asdict(score_def.hist_conf)
                    if score_def.hist_conf else "null",
                }
                for score_def in self.gene_score.score_definitions.values()
            ],
            "score_file": manifest[score_filename].md5,
        }, sort_keys=True, indent=2).encode()


def build_gene_score_implementation_from_resource(
        resource: GenomicResource) -> GenomicResourceImplementation:
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneScoreImplementation(resource)


GENE_SCORES_TEMPLATE = """
{% extends base %}
{% block content %}
{% set score = data.gene_score %}
<hr>
    <h3>Gene scores file:</h3>
    <a href="{{ score.filename }}">
        {{ score.filename }}
    </a>

    <h3>Gene score definitions:</h3>
    {% for score_def in score.score_definitions.values() %}
        <div class="score-definition">
            <p>Gene score ID: {{ score_def.score_id }}</p>
            <p>Description: {{ score_def.description }}
        </div>
    {% endfor %}
    <h3>Histograms:</h3>
    {% for score_id in score.score_definitions.keys() %}
    {% set hist = score.get_score_histogram(score_id) %}

    {% if hist %}
        <div class="histogram">
            <h4>{{ score_id }}</h4>
            <img src="{{score.get_histogram_image_filename(score_id) }}"
            width="200px"
            alt={{ score_id }}
            title={{ score_id }}>
        </div>
    {% endif %}
{% endfor %}
{% endblock %}
"""
