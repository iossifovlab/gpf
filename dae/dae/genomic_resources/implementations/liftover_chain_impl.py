"""Provides LiftOver chain resource."""

from __future__ import annotations

import copy
import logging
import textwrap
from typing import Any

from jinja2 import Template
from markdown2 import markdown

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class LiftoverChainImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin,
):
    """Defines Lift Over chain resource implementation."""

    def __init__(self, resource: GenomicResource):

        super().__init__(resource)
        self.liftover_chain = build_liftover_chain_from_resource(self.resource)

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <hr>
            <h3>Liftover chain file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>
            <p>Format: {{ data["format"] }}</p>
            {% if data["variant_chrom"] %}
            <p>{{ data["variant_chrom"] }}</p>
            {% endif %}
            {% if data["target_chrom"] %}
            <p>{{ data["target_chrom"] }}</p>
            {% endif %}
            {% endblock %}
        """))

    def _get_template_data(self) -> dict[str, Any]:
        info = copy.deepcopy(self.config)

        if self.liftover_chain.chrom_variant_coordinates is not None:
            if "del_prefix" in self.liftover_chain.chrom_variant_coordinates:
                prefix = self.liftover_chain\
                    .chrom_variant_coordinates["del_prefix"]
                info["variant_chrom"] = (
                    f"Deletes chrom prefix {prefix}"
                    " from variants before performing liftover."
                )
            elif "add_prefix" in self.liftover_chain.chrom_variant_coordinates:
                prefix = self.liftover_chain\
                    .chrom_variant_coordinates["add_prefix"]
                info["variant_chrom"] = (
                    f"Adds chrom prefix {prefix}"
                    " to variants before performing liftover."
                )

        if self.liftover_chain.chrom_target_coordinates is not None:
            if "del_prefix" in self.liftover_chain.chrom_target_coordinates:
                prefix = self.liftover_chain\
                    .chrom_target_coordinates["del_prefix"]
                info["target_chrom"] = (
                    f"Deletes chrom prefix {prefix}"
                    " from variants after performing liftover."
                )
            elif "add_prefix" in self.liftover_chain.chrom_target_coordinates:
                prefix = self.liftover_chain\
                    .chrom_target_coordinates["add_prefix"]
                info["target_chrom"] = (
                    f"Adds chrom prefix {prefix}"
                    " to variants after performing liftover."
                )
        if "meta" in info:
            info["meta"] = markdown(str(info["meta"]))
        return info

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(
            self, task_graph: TaskGraph,
            **kwargs: str | None) -> list[Task]:
        return []
