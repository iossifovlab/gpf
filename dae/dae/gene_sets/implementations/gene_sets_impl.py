import copy
import json
from collections import Counter
from functools import lru_cache
from typing import Any

from jinja2 import Template
from markdown2 import markdown

from dae.gene_sets.gene_sets_db import build_gene_set_collection_from_resource
from dae.genomic_resources.histogram import (
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
    """Class used to represent gene sets collection resource implementations."""

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
                [],
                [],
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
    ) -> NumberHistogram:
        gene_set_collection = build_gene_set_collection_from_resource(resource)
        all_gene_sets = gene_set_collection.get_all_gene_sets()
        config = (
            gene_set_collection.config.model_dump()
            if gene_set_collection.config
            else {}
        )
        histograms = config.get("histograms") or {}
        hist_conf_data = histograms.get("genes_per_gene_set") or {}
        hist_conf = (
            NumberHistogramConfig.from_dict(hist_conf_data)
            if hist_conf_data else None
        )

        if hist_conf is None:
            min_count = min(all_gene_sets, key=lambda gs: gs.count).count
            max_count = max(all_gene_sets, key=lambda gs: gs.count).count
            hist_conf = NumberHistogramConfig(view_range=(min_count, max_count))

        histogram = NumberHistogram(hist_conf)

        for gs in all_gene_sets:
            histogram.add_value(gs.count)

        return histogram

    @staticmethod
    def _calc_gene_sets_per_gene_hist(
        resource: GenomicResource,
    ) -> NumberHistogram:
        gene_set_collection = build_gene_set_collection_from_resource(resource)
        all_gene_sets = gene_set_collection.get_all_gene_sets()

        config = (
            gene_set_collection.config.model_dump()
            if gene_set_collection.config
            else {}
        )
        histograms = config.get("histograms") or {}
        hist_conf_data = histograms.get("gene_sets_per_gene", {})
        hist_conf = (
            NumberHistogramConfig.from_dict(hist_conf_data)
            if hist_conf_data else None
        )

        gene_counter = Counter(
            gene for gs in all_gene_sets for gene in set(gs.syms)
        )

        if hist_conf is None:
            max_gene_count = max(gene_counter.values(), default=0)
            hist_conf = NumberHistogramConfig(view_range=(0, max_gene_count))

        histogram = NumberHistogram(hist_conf)

        for count in gene_counter.values():
            histogram.add_value(count)

        return histogram

    @staticmethod
    def _save_genes_per_gene_set_hist(
        histogram: NumberHistogram,
        resource: GenomicResource,
    ) -> NumberHistogram:
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
            "genes per gene set",
        )
        return histogram

    @staticmethod
    def _save_gene_sets_per_gene_hist(
        histogram: NumberHistogram,
        resource: GenomicResource,
    ) -> NumberHistogram:
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
            "gene sets per gene",
        )
        return histogram

    @lru_cache(maxsize=64)
    def get_gene_collection_count_statistics(self) -> dict | None:  # pylint: disable=missing-function-docstring
        try:
            with self.resource.proto.open_raw_file(
                self.resource,
                "statistics/gene_collection_count_statistics.json",
                "rt",
            ) as statistics_file:
                return json.load(statistics_file)
        except FileNotFoundError:
            return None

    @staticmethod
    def get_schema():
        raise NotImplementedError


def build_gene_set_collection_implementation_from_resource(
    resource: GenomicResource,
) -> GenomicResourceImplementation:
    if resource is None:
        raise ValueError(f"missing resource {resource}")
    return GeneSetCollectionImpl(resource)


GENE_SETS_TEMPLATE = """
{% extends base %}
{% block content %}
{% set gene_set_collection = data.gene_set_collection %}
<hr>
<h2>Gene set ID: {{ data["id"] }}</h2>
{% if data["format"] == "directory" %}
<h3>Gene sets directory:</h3>
<a href="{{ data["directory"] }}">{{ data["directory"] }}</a>
{% else %}
<h3>Gene sets file:</h3>
<a href="{{ data["filename"] }}">{{ data["filename"] }}</a>
{% endif %}
<p>Format: {{ data["format"] }}</p>
{% if data["web_label"] %}<p>Web label: {{ data["web_label"] }}</p>{% endif %}
{% if data["web_format_str"] %}
<p>Web label: {{ data["web_format_str"] }}</p>
<p>Number of gene sets: {{ data["number_of_gene_sets"] }}</p>
<p>Number of unique genes: {{ data["number_of_unique_genes"] }}</p>
{% endif %}
<div class="histogram">
    <img src="{{ gene_set_collection.get_genes_per_gene_set_hist_filename() }}"
        style="width: 200px; cursor: pointer;"
        alt={{ data["id"] }}
        title="genes-per-gene-set"
        data-modal-trigger="genes-per-gene-set">
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
<div class="histogram">
    <img src="{{ gene_set_collection.get_gene_sets_per_gene_hist_filename() }}"
        style="width: 200px; cursor: pointer;"
        alt={{ data["id"] }}
        title="gene-sets-per-gene"
        data-modal-trigger="gene-sets-per-gene">
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
{% endblock %}
"""  # noqa: E501
