"""Provides LiftOver chain resource."""

from __future__ import annotations
from typing import Optional

import logging

from pyliftover import LiftOver  # type: ignore

from dae.genomic_resources import GenomicResource


logger = logging.getLogger(__name__)


class LiftoverChain:
    """Defines Lift Over chain wrapper around pyliftover objects."""

    def __init__(self, resource: GenomicResource):

        config = resource.get_config()
        if resource.get_type() != "liftover_chain":
            logger.error(
                "trying to use genomic resource %s "
                "as a liftover chaing but its type is %s; %s",
                resource.resource_id, resource.get_type(), config)
            raise ValueError(f"wrong resource type: {config}")

        self.resource = resource

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


def load_liftover_chain_from_resource(
        resource: GenomicResource) -> LiftoverChain:
    """Load a Lift Over chaing from GRR resource."""
    config: dict = resource.get_config()

    if resource.get_type() != "liftover_chain":
        logger.error(
            "trying to use genomic resource %s "
            "as a liftover chaing but its type is %s; %s",
            resource.resource_id, resource.get_type(), config)
        raise ValueError(f"wrong resource type: {config}")

    result = LiftoverChain(resource)
    result.open()
    return result
