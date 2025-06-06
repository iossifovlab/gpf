"""Provides LiftOver chain resource."""

from __future__ import annotations

import logging
from typing import Any, cast

from pyliftover import LiftOver  # type: ignore

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)

logger = logging.getLogger(__name__)


class LiftoverChain(ResourceConfigValidationMixin):
    """Defines Lift Over chain wrapper around pyliftover objects."""

    def __init__(self, resource: GenomicResource):

        self.resource = resource
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

        self.liftover: LiftOver | None = None

        self.source_genome_id: str | None = None
        self.target_genome_id: str | None = None

        if config.get("meta") is not None \
           and config["meta"].get("labels") is not None:
            labels = config["meta"]["labels"]
            self.source_genome_id = labels.get("source_genome")
            self.target_genome_id = labels.get("target_genome")

    def close(self) -> None:
        if self.liftover is not None:
            del self.liftover
            self.liftover = None

    def open(self) -> LiftoverChain:
        filename: str = self.resource.get_config()["filename"]
        with self.resource.open_raw_file(
                filename, "rb", compression=True) as chain_file:
            self.liftover = LiftOver(chain_file)
        return self

    def is_open(self) -> bool:
        return self.liftover is not None

    @property
    def files(self) -> set[str]:
        return {self.resource.get_config()["filename"]}

    @staticmethod
    def map_chromosome(chrom: str, mapping: dict[str, str] | None) -> str:
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

    def convert_coordinate(
        self, chrom: str,
        pos: int,
    ) -> tuple[str, int, str, int] | None:
        """Lift over a genomic coordinate."""
        chrom = self.map_chromosome(chrom, self.chrom_variant_coordinates)
        assert self.liftover is not None
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
        coordinates[1] += 1
        assert coordinates[2] in {"+", "-"}
        return cast(tuple[str, int, str, int], tuple(coordinates))

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "chrom_prefix": {"type": "dict", "schema": {
                "variant_coordinates": {"type": "dict", "schema": {
                    "del_prefix": {"type": "string"},
                    "add_prefix": {"type": "string"},
                }},
                "target_coordinates": {"type": "dict", "schema": {
                    "del_prefix": {"type": "string"},
                    "add_prefix": {"type": "string"},
                }},
            }},
        }


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

    return LiftoverChain(resource)


def build_liftover_chain_from_resource_id(
    resource_id: str, grr: GenomicResourceRepo | None = None,
) -> LiftoverChain:
    if grr is None:
        grr = build_genomic_resource_repository()
    return build_liftover_chain_from_resource(
        grr.get_resource(resource_id))
