"""Provides LiftOver chain resource."""

from __future__ import annotations
from typing import Optional
import copy
import textwrap

import logging

from pyliftover import LiftOver  # type: ignore

from jinja2 import Template
from markdown2 import markdown
from cerberus import Validator

from dae.genomic_resources import GenomicResource

from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema, \
    InfoImplementationMixin, ResourceConfigValidationMixin


logger = logging.getLogger(__name__)


class LiftoverChain(
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin
):
    """Defines Lift Over chain wrapper around pyliftover objects."""

    config_validator = Validator

    def __init__(self, resource: GenomicResource):

        super().__init__(resource)

        config = resource.get_config()
        if resource.get_type() != "liftover_chain":
            logger.error(
                "trying to use genomic resource %s "
                "as a liftover chain but its type is %s; %s",
                resource.resource_id, resource.get_type(), config)
            raise ValueError(f"wrong resource type: {config}")

        chrom_prefix = config.get("chrom_prefix")
        if chrom_prefix is None:
            self.chrom_variant_coordinates = None
            self.chrom_target_coordinates = None
        else:
            self.chrom_variant_coordinates = chrom_prefix.get(
                "variant_coordinates", None)
            self.chrom_target_coordinates = chrom_prefix.get(
                "target_coordinates", None)

        self.liftover: Optional[LiftOver] = None

    def close(self):
        del self.liftover
        self.liftover = None

    def open(self) -> LiftoverChain:
        filename: str = self.resource.get_config()["filename"]
        with self.resource.open_raw_file(
                filename, "rb", compression=True) as chain_file:
            self.liftover = LiftOver(chain_file)
        return self

    def is_open(self):
        return self.liftover is not None

    @property
    def files(self):
        return {self.resource.get_config()["filename"], }

    @staticmethod
    def map_chromosome(chrom, mapping):
        """Map a chromosome (contig) name according to configuration."""
        if not mapping:
            return chrom
        if "del_prefix" in mapping:
            del_prefix = mapping["del_prefix"]
            if chrom.startswith(del_prefix):
                chrom = chrom.lstrip(del_prefix)
        if "add_prefix" in mapping:
            add_prefix = mapping["add_prefix"]
            chrom = f"{add_prefix}{chrom}"
        return chrom

    def convert_coordinate(self, chrom, pos):
        """Lift over a genomic coordinate."""
        chrom = self.map_chromosome(chrom, self.chrom_variant_coordinates)

        lo_coordinates = self.liftover.convert_coordinate(chrom, pos - 1)

        if not lo_coordinates:
            return None
        if len(lo_coordinates) > 1:
            logger.info(
                "liftover_variant: liftover returns more than one target "
                "position: %s", lo_coordinates)

        coordinates = list(lo_coordinates[0])
        coordinates[0] = self.map_chromosome(
            coordinates[0], self.chrom_target_coordinates)

        return tuple(coordinates)

    @staticmethod
    def get_template():
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

    def _get_template_data(self):
        info = copy.deepcopy(self.config)

        if self.chrom_variant_coordinates is not None:
            if "del_prefix" in self.chrom_variant_coordinates:
                prefix = self.chrom_variant_coordinates["del_prefix"]
                info["variant_chrom"] = (
                    f"Deletes chrom prefix {prefix}"
                    " from variants before performing liftover."
                )
            elif "add_prefix" in self.chrom_variant_coordinates:
                prefix = self.chrom_variant_coordinates["add_prefix"]
                info["variant_chrom"] = (
                    f"Adds chrom prefix {prefix}"
                    " to variants before performing liftover."
                )

        if self.chrom_target_coordinates is not None:
            if "del_prefix" in self.chrom_target_coordinates:
                prefix = self.chrom_target_coordinates["del_prefix"]
                info["target_chrom"] = (
                    f"Deletes chrom prefix {prefix}"
                    " from variants after performing liftover."
                )
            elif "add_prefix" in self.chrom_target_coordinates:
                prefix = self.chrom_target_coordinates["add_prefix"]
                info["target_chrom"] = (
                    f"Adds chrom prefix {prefix}"
                    " to variants after performing liftover."
                )
        if "meta" in info:
            info["meta"] = markdown(info["meta"])
        return info

    @staticmethod
    def get_schema():
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "chrom_prefix": {"type": "dict", "schema": {
                "variant_coordinates": {"type": "dict", "schema": {
                    "del_prefix": {"type": "string"},
                    "add_prefix": {"type": "string"}
                }},
                "target_coordinates": {"type": "dict", "schema": {
                    "del_prefix": {"type": "string"},
                    "add_prefix": {"type": "string"}
                }}
            }}
        }

    def get_info(self):
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self):
        return "placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(self, task_graph, **kwargs) -> None:
        return


def build_liftover_chain_from_resource(
        resource: GenomicResource) -> LiftoverChain:
    """Load a Lift Over chain from GRR resource."""
    config: dict = resource.get_config()

    if resource.get_type() != "liftover_chain":
        logger.error(
            "trying to use genomic resource %s "
            "as a liftover chaing but its type is %s; %s",
            resource.resource_id, resource.get_type(), config)
        raise ValueError(f"wrong resource type: {config}")

    result = LiftoverChain(resource)
    return result
