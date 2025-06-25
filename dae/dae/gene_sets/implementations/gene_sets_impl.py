import copy
import json
from collections import Counter
from functools import lru_cache
from typing import Any, cast

from jinja2 import Template
from markdown2 import markdown

from dae.gene_sets.gene_sets_db import build_gene_set_collection_from_resource
from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
    plot_histogram,
)
from dae.genomic_resources.repository import (
    GenomicResource,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin,
)
from dae.task_graph.graph import Task, TaskGraph


class GeneSetCollectionImpl(
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin,
):
    """Gene sets collection resource implementations."""

    def __init__(self, resource: GenomicResource) -> None:
        super().__init__(resource)

        config = resource.get_config()
        if config is None:
            raise ValueError(
                f"genomic resource {resource.resource_id} not configured")
        self.gene_set_collection = build_gene_set_collection_from_resource(
            resource,
        )

    def get_template(self) -> Template:
        return Template(GENE_SETS_TEMPLATE)

    @staticmethod
    def _compute_gene_statistics(resource: GenomicResource) -> dict:
        gene_set_collection = build_gene_set_collection_from_resource(resource)

        all_gene_sets = gene_set_collection.get_all_gene_sets()
        unique_genes = set()
        for gene_set in all_gene_sets:
            unique_genes.update(gene_set.syms)

        result = {
            "number_of_gene_sets": len(all_gene_sets),
            "number_of_unique_genes": len(unique_genes),
        }

        with resource.proto.open_raw_file(
            resource,
            "statistics/gene_collection_count_statistics.json",
            "wt",
        ) as statistics_file:
            json.dump(result, statistics_file)

        return result

    def _get_template_data(self) -> dict:
        info = copy.deepcopy(self.config)
        if "meta" in info:
            info["meta"] = markdown(str(info["meta"]))

        info["gene_set_collection"] = self.gene_set_collection

        statistics = self.get_gene_collection_count_statistics()
        if statistics is not None:
            info["number_of_gene_sets"] = (
                statistics["number_of_gene_sets"]
            )
            info["number_of_unique_genes"] = (
                statistics["number_of_unique_genes"]
            )
        else:
            info["number_of_gene_sets"] = "?"
            info["number_of_unique_genes"] = "?"

        return info

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any,  # noqa: ARG002
    ) -> list[Task]:
        return [
            task_graph.create_task(
                f"{self.resource.resource_id}_calc_and_save_statistics",
                self._calc_and_save_statistics,
                args=[],
                deps=[],
            ),
        ]

    def _calc_and_save_statistics(self) -> None:
        hist = self._calc_genes_per_gene_set_hist(self.resource)
        self._save_genes_per_gene_set_hist(hist, self.resource)
        hist = self._calc_gene_sets_per_gene_hist(self.resource)
        self._save_gene_sets_per_gene_hist(hist, self.resource)
        self._compute_gene_statistics(self.gene_set_collection.resource)

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def get_statistics_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_statistics_info(self)

    @staticmethod
    def _calc_genes_per_gene_set_hist(
        resource: GenomicResource,
    ) -> NumberHistogram | CategoricalHistogram:
        gene_set_collection = build_gene_set_collection_from_resource(resource)

        config = gene_set_collection.config
        genes_per_gene_set_schema = (
            config.histograms.get("genes_per_gene_set")
            if config and config.histograms
            else None
        )

        hist_config = (
            genes_per_gene_set_schema.model_dump(exclude_unset=True)
            if genes_per_gene_set_schema
            else {}
        )

        histogram: NumberHistogram | CategoricalHistogram

        if hist_config.get("type") == "number":
            view_range = []
            if hist_config.get("view_range") is None:
                all_gene_sets = gene_set_collection.get_all_gene_sets()
                min_count = min(all_gene_sets, key=lambda gs: gs.count).count
                max_count = max(all_gene_sets, key=lambda gs: gs.count).count
                view_range = [min_count, max_count]
            else:
                view_range = [
                    hist_config["view_range"].get("min"),
                    hist_config["view_range"].get("max"),
                ]

            hist_config["view_range"] = view_range
            hist_config.pop("type", None)

            histogram = NumberHistogram(
                NumberHistogramConfig(
                    **hist_config,
                ),
            )
        else:
            hist_config.pop("type", None)
            hist_config["allow_only_whole_values_y"] = True
            histogram = CategoricalHistogram(
                CategoricalHistogramConfig(**hist_config))

        for gs in gene_set_collection.get_all_gene_sets():
            histogram.add_value(gs.count)

        return histogram

    @staticmethod
    def _calc_gene_sets_per_gene_hist(
        resource: GenomicResource,
    ) -> NumberHistogram | CategoricalHistogram:
        gene_set_collection = build_gene_set_collection_from_resource(resource)

        gs_config = gene_set_collection.config
        gene_sets_per_gene_schema = (
            gs_config.histograms.get("gene_sets_per_gene")
            if gs_config and gs_config.histograms
            else None
        )

        hist_config = (
            gene_sets_per_gene_schema.model_dump(exclude_unset=True)
            if gene_sets_per_gene_schema
            else {}
        )
        histogram: NumberHistogram | CategoricalHistogram

        if hist_config.get("type") == "number":
            view_range = []
            if hist_config.get("view_range") is None:
                all_gene_sets = gene_set_collection.get_all_gene_sets()
                gene_counter = Counter(
                    gene for gs in all_gene_sets for gene in set(gs.syms)
                )
                max_gene_count = max(gene_counter.values(), default=0)
                view_range = [0, max_gene_count]
            else:
                view_range = [
                    hist_config["view_range"].get("min"),
                    hist_config["view_range"].get("max"),
                ]

            hist_config["view_range"] = view_range
            hist_config.pop("type", None)
            histogram = NumberHistogram(
                NumberHistogramConfig(
                    **hist_config,
                ),
            )
        else:
            hist_config.pop("type", None)
            histogram = CategoricalHistogram(
                CategoricalHistogramConfig(**hist_config))

        gene_counter = Counter(
            gene
            for gs in gene_set_collection.get_all_gene_sets()
            for gene in set(gs.syms)
        )

        for count in gene_counter.values():
            histogram.add_value(count)

        return histogram

    @staticmethod
    def _save_genes_per_gene_set_hist(
        histogram: CategoricalHistogram | NumberHistogram,
        resource: GenomicResource,
    ) -> CategoricalHistogram | NumberHistogram:
        proto = resource.proto
        gene_set_collection = build_gene_set_collection_from_resource(resource)

        with proto.open_raw_file(
            resource,
            "statistics/genes_per_gene_set_histogram.json",
            mode="wt",
        ) as outfile:
            outfile.write(histogram.serialize())

        plot_histogram(
            resource,
            gene_set_collection.get_genes_per_gene_set_hist_filename(),
            histogram,
            "gene count per gene set",
            "count of gene sets",
        )
        return histogram

    @staticmethod
    def _save_gene_sets_per_gene_hist(
        histogram: CategoricalHistogram | NumberHistogram,
        resource: GenomicResource,
    ) -> CategoricalHistogram | NumberHistogram:
        proto = resource.proto
        gene_set_collection = build_gene_set_collection_from_resource(resource)

        with proto.open_raw_file(
            resource,
            "statistics/gene_sets_per_gene_histogram.json",
            mode="wt",
        ) as outfile:
            outfile.write(histogram.serialize())

        plot_histogram(
            resource,
            gene_set_collection.get_gene_sets_per_gene_hist_filename(),
            histogram,
            "number of gene sets the gene is present in",
            "number of genes",
        )
        return histogram

    @lru_cache(maxsize=64)
    def get_gene_collection_count_statistics(self) -> dict | None:
        """Get gene collection count statistics from the resource."""
        try:
            with self.resource.proto.open_raw_file(
                self.resource,
                "statistics/gene_collection_count_statistics.json",
                "rt",
            ) as statistics_file:
                return cast(dict, json.load(statistics_file))
        except FileNotFoundError:
            return None

    @staticmethod
    def get_schema() -> dict[str, Any]:
        raise NotImplementedError


def build_gene_set_collection_implementation_from_resource(
    resource: GenomicResource,
) -> GenomicResourceImplementation:
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneSetCollectionImpl(resource)


GENE_SETS_TEMPLATE = """
{% extends base %}
{% block extra_styles %}
#gene-sets-table {
    border-collapse: separate;
    border-spacing: 0;
    width: 1200px;
    table-layout: fixed;
}
#gene-sets-table th {
    word-break: break-word;
    max-width: 200px;
    border-top: 1px solid;
    border-bottom: 1px solid;
    border-right: 1px solid;
}
#gene-sets-table td {
    word-break: break-word;
    max-width: 200px;
    border-bottom: 1px solid;
    border-right: 1px solid;
}
#gene-sets-table th:first-child,
#gene-sets-table td:first-child {
    border-left: 1px solid;
}
#gene-sets-table thead tr:nth-of-type(2) th {
    border-top: none;
}
#gene-sets-table thead {
    position: sticky; top: 0; background-color: white;
}
.histogram {
    margin-bottom: 16px;
}
{% endblock %}

{% block content %}
{% set gene_set_collection = data.gene_set_collection %}
<hr>
<h2>Gene set ID: {{ data["id"] }}</h2>
<h3>Statistics:</h3>
<p>Number of gene sets: {{ data["number_of_gene_sets"] }}</p>
<p>Number of unique genes: {{ data["number_of_unique_genes"] }}</p>
<div style="display: flex; padding-top: 8px;">
    <div style="display: flex; flex-direction: column; align-items: center;">
        <span>Count of genes per gene set</span>
        <div class="histogram">
            <img src="{{ gene_set_collection.get_genes_per_gene_set_hist_filename() }}"
                style="width: 300px; cursor: pointer;"
                alt={{ data["id"] }}
                title="genes-per-gene-set"
                data-modal-trigger="genes-per-gene-set">
        </div>
    </div>
    <div style="display: flex; flex-direction: column; align-items: center; padding-left: 38px;">
        <span>Count of gene sets per gene</span>
        <div class="histogram">
            <img src="{{ gene_set_collection.get_gene_sets_per_gene_hist_filename() }}"
                style="width: 300px; cursor: pointer;"
                alt={{ data["id"] }}
                title="gene-sets-per-gene"
                data-modal-trigger="gene-sets-per-gene">
        </div>
    </div>
</div>
<div id="genes-per-gene-set" class="modal">
    <div class="modal-content"
        style="padding: 10px 20px; background-color: #fff; height: fit-content; width: fit-content;">
        <span class="close">&times;</span>
        <img src="{{ gene_set_collection.get_genes_per_gene_set_hist_filename() }}"
            alt="genes per gene set histogram"
            title="genes-per-gene-set">
    </div>
</div>
<div id="gene-sets-per-gene" class="modal">
    <div class="modal-content"
        style="padding: 10px 20px; background-color: #fff; height: fit-content; width: fit-content;">
        <span class="close">&times;</span>
        <img src="{{ gene_set_collection.get_gene_sets_per_gene_hist_filename() }}"
            alt="genes per gene set histogram"
            title="gene-sets-per-gene">
    </div>
</div>
<div style="max-height: 50%; overflow-y: auto; width: fit-content; margin-bottom: 16px;">
    <table id="gene-sets-table">
        <thead>
            <tr>
                <th>Gene Set</th>
                <th style="width: 110px">Gene Count</th>
                <th>Description</th>
            </tr>
        </thead>
        {%- for gene_set in gene_set_collection.get_all_gene_sets() | sort(attribute="count", reverse=true) -%}
            <tr>
                <td>{{ gene_set["name"] }}</td>
                <td>{{ gene_set["count"] }}</td>
                <td>{{ gene_set["desc"] if gene_set["desc"] else gene_set["name"] }}</td>
            </tr>
        {%- endfor -%}
    </table>
</div>
{% if data["format"] == "directory" %}
<h3>Gene sets directory:</h3>
<a href="{{ data["directory"] }}">{{ data["directory"] }}</a>
{% else %}
<h3 style="margin-top: 32px">Gene sets file:</h3>
<a href="{{ data["filename"] }}">{{ data["filename"] }}</a>
{% endif %}
<p>Format: {{ data["format"] }}</p>
{% if data["web_label"] %}<p>Web label: {{ data["web_label"] }}</p>{% endif %}
{% if data["web_format_str"] %}
<p>Web label: {{ data["web_format_str"] }}</p>
{% endif %}
{% endblock %}
"""  # noqa: E501
