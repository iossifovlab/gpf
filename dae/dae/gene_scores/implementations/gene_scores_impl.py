from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict
from typing import Any

from jinja2 import Template

from dae.gene_scores.gene_scores import (
    GeneScore,
    GeneScoresDb,
    build_gene_score_from_resource,
)
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
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
        self, task_graph: TaskGraph,
        **kwargs: str,  # noqa: ARG002
    ) -> list[Task]:
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
        resource: GenomicResource, score_id: str,
    ) -> NumberHistogram | CategoricalHistogram:
        score = build_gene_score_from_resource(resource)
        hist_conf = score.score_definitions[score_id].hist_conf

        histogram: NumberHistogram | CategoricalHistogram

        if isinstance(hist_conf, NumberHistogramConfig):
            histogram = NumberHistogram(hist_conf)
            for value in score.get_values(score_id):
                histogram.add_value(value)
        elif isinstance(hist_conf, CategoricalHistogramConfig):
            histogram = CategoricalHistogram(hist_conf)
            for value in score.get_values(score_id):
                if math.isnan(value):
                    continue
                histogram.add_value(int(value))

        return histogram

    @staticmethod
    def _save_histogram(
        histogram: NumberHistogram | CategoricalHistogram,
        resource: GenomicResource,
        score_id: str,
    ) -> NumberHistogram | CategoricalHistogram:
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
            scores_db = GeneScoresDb([gene_score])
            score_desc = scores_db.get_score_desc(score_id)
            small_values_desc = None
            large_values_desc = None
            if score_desc is not None:
                small_values_desc = score_desc.small_values_desc
                large_values_desc = score_desc.large_values_desc
            histogram.plot(
                outfile,
                score_id,
                small_values_desc,
                large_values_desc,
            )
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

<style>
    .modal {
        display: none;
        position: fixed;
        z-index: 1;
        padding-top: 100px;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        justify-content: center;
    }
    .modal-content {
        margin: auto;
        display: block;
        width: 80%;
        max-width: 700px;
    }
    .close {
        float: right;
        font-size: 40px;
        font-weight: bold;
    }
    .close:hover,
    .close:focus {
         color: #bbb;
         text-decoration: none;
         cursor: pointer;
    }
</style>
{% block javascript %}
    <script type="text/javascript">
        function openModal(scoreId) {
            var modal = document.getElementById("modal-" + scoreId);
            modal.style.display = "flex";
        }
        function closeModal(scoreId) {
            var modal = document.getElementById("modal-" + scoreId);
            modal.style.display = "none";
        }
    </script>
{% endblock %}

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
                    <div>{{ score_def.desc }}</div>
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
                            width="200px"
                            alt={{ score_id }}
                            title={{ score_id | replace(" ", "_")}}
                            style="cursor: pointer"
                            onclick="openModal(title)">>
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
            <div id="modal-{{score_id | replace(" ", "_")}}" class="modal">
                <div style="padding: 10px 20px; background-color: #fff; height: fit-content; width: fit-content;">
                    <span title={{score_id | replace(" ", "_")}} class="close" onclick="closeModal(title)">&times;</span>
                    <img class="modal-content" id="histogram-{{score_id}}"
                        src="{{ score.get_histogram_image_filename(score_id) }}"
                        alt="{{ "HISTOGRAM FOR " + score_id }}"
                        title={{ score_id | replace(" ", "_")}}
                        width="200">
                </div>
            </div>
        {%- endfor %}
    </table>
{% endblock %}
"""  # noqa: E501
