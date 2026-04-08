from __future__ import annotations

import json
import logging
import math
from typing import Any

from jinja2 import Template

from gain.gene_scores.gene_scores import (
    GeneScore,
    GeneScoresDb,
    build_gene_score_from_resource,
)
from gain.genomic_resources import GenomicResource
from gain.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    NullHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
    plot_histogram,
)
from gain.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from gain.task_graph.graph import TaskDesc, TaskGraph

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

    def get_statistics_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_statistics_info(self)

    def create_statistics_build_tasks(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> list[TaskDesc]:
        create_task = TaskGraph.make_task(
            f"{self.resource.resource_id}_build_histograms",
            self._build_histograms,
            args=[self.resource],
            deps=[],
        )
        return [create_task]

    @staticmethod
    def _build_histograms(
        resource: GenomicResource,
    ) -> dict[str, NumberHistogram | CategoricalHistogram]:
        histograms = {}
        gene_score = build_gene_score_from_resource(resource)
        for score_id in gene_score.score_definitions:
            try:
                histogram = GeneScoreImplementation._calc_histogram(
                    gene_score, score_id)
            except ValueError as e:
                logger.warning(
                    "Error calculating histogram for score %s in %s: %s",
                    score_id, resource.resource_id, e,
                )
                continue

            if histogram is None:
                logger.warning(
                    "Gene score %s in %s has no histogram config!",
                    score_id, resource.resource_id,
                )
                continue

            with resource.proto.open_raw_file(
                resource,
                gene_score.get_histogram_filename(score_id),
                mode="wt",
            ) as outfile:
                outfile.write(histogram.serialize())
            scores_db = GeneScoresDb([gene_score])
            score_desc = scores_db.get_score_desc(score_id)
            small_values_desc = None
            large_values_desc = None
            if score_desc is not None:
                small_values_desc = score_desc.small_values_desc
                large_values_desc = score_desc.large_values_desc
            plot_histogram(
                resource,
                gene_score.get_histogram_image_filename(score_id),
                histogram,
                score_id,
                small_values_desc,
                large_values_desc,
            )
            histograms[score_id] = histogram
        return histograms

    @staticmethod
    def _calc_histogram(
        gene_score: GeneScore, score_id: str,
    ) -> NumberHistogram | CategoricalHistogram | None:
        if score_id not in gene_score.score_definitions:
            raise ValueError(
                f"Score ID {score_id} not found in gene score definitions")
        score_def = gene_score.score_definitions.get(score_id)
        assert score_def is not None
        hist_conf = score_def.hist_conf
        if hist_conf is None or isinstance(hist_conf, NullHistogramConfig):
            return None
        histogram: NumberHistogram | CategoricalHistogram

        if isinstance(hist_conf, NumberHistogramConfig):
            histogram = NumberHistogram(hist_conf)
            for value in gene_score.get_values(score_id):
                histogram.add_value(value)
        elif isinstance(hist_conf, CategoricalHistogramConfig):
            histogram = CategoricalHistogram(hist_conf)
            for value in gene_score.get_values(score_id):
                if math.isnan(value):
                    continue
                histogram.add_value(int(value))
        else:
            raise TypeError(f"Unknown histogram config: {hist_conf}")
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
                    "hist_conf": score_def.hist_conf.to_dict()
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

<h1>Scores</h1>
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Description</th>
            <th>Histograms</th>
            <th>Range</th>
        </tr>

        {% for score_id, score_def in score.score_definitions.items() %}
            <tr>
                <td>{{ score_id }}</td>

                <td>{{ score.value_type }}</td>

                <td>
                    <div>{{ score_def.description }}</div>
                    {% if score_def.small_values_desc %}
                        <div style="color: rgb(145,145,145)">
                            {{ "Small values desc: " + score_def.small_values_desc }}
                        </div>
                    {% endif %}
                    {% if score_def.large_values_desc %}
                        <div style="color: rgb(145,145,145)">
                            {{ "Large values desc: " + score_def.large_values_desc }}
                        </div>
                    {% endif %}
                </td>

                {% set hist = score.get_score_histogram(score_id) %}
                <td>
                {% if hist %}
                    <div class="histogram">
                        <img src="{{score.get_histogram_image_filename(score_id)}}"
                            style="width: 200px; cursor: pointer;"
                            alt={{ score_id }}
                            title=" {{ score_id | replace(" ", "_") }}"
                            data-modal-trigger="modal-{{ score_id | replace(" ", "_") }}">
                    </div>
                {% endif %}
                </td>

                <td>
                {%- if hist.type != 'null_histogram' %}
                    {{ hist.values_domain() }}
                {%- else -%}
                    NO DOMAIN
                {%- endif -%}
                </td>
            </tr>
        {% endfor %}

        {%- for score_id in score.score_definitions.keys() -%}
            <div id="modal-{{ score_id | replace(" ", "_") }}" class="modal">
                <div class="modal-content"
                    style="padding: 10px 20px; background-color: #fff; height: fit-content; width: fit-content;">
                    <span class="close">&times;</span>
                    <img src="{{ score.get_histogram_image_filename(score_id) }}"
                        alt="{{ "HISTOGRAM FOR " + score_id }}"
                        title="{{ score_id | replace(" ", "_") }}">
                </div>
            </div>
        {%- endfor %}
    </table>
{% endblock %}
"""  # noqa: E501
