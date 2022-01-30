from __future__ import annotations
from typing import TextIO

from dae.genomic_resources import GenomicResource
import logging

from pyliftover import LiftOver  # type: ignore

logger = logging.getLogger(__name__)


class LiftoverChain:

    def __init__(self, config: dict, chain_file: TextIO):

        chrom_prefix = config.get("chrom_prefix")
        if chrom_prefix is None:
            self.chrom_variant_coordinates = None
            self.chrom_target_coordinates = None
        else:
            self.chrom_variant_coordinates = chrom_prefix.get(
                'variant_coordinates', None)
            self.chrom_target_coordinates = chrom_prefix.get(
                'target_coordinates', None)

        self.chain_file = chain_file
        self.liftover = LiftOver(self.chain_file)

    @classmethod
    def get_resource_type(clazz):
        return "liftover_chain"

    def close(self):
        pass

    def map_chromosome(self, chrom, mapping):
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
        chrom = self.map_chromosome(chrom, self.chrom_variant_coordinates)

        lo_coordinates = self.liftover.convert_coordinate(chrom, pos - 1)

        if not lo_coordinates:
            return None
        if len(lo_coordinates) > 1:
            logger.info(
                f"liftover_variant: liftover returns more than one target "
                f"position: {lo_coordinates}")

        coordinates = list(lo_coordinates[0])
        coordinates[0] = self.map_chromosome(
            coordinates[0], self.chrom_target_coordinates)

        return tuple(coordinates)


def load_liftover_chain_from_resource(
        resource: GenomicResource) -> LiftoverChain:

    config: dict = resource.get_config()

    if resource.get_type() != "liftover_chain":
        logger.error(
            f"trying to use genomic resource {resource.resource_id} "
            f"as a liftover chaing but its type is {resource.get_type()}; "
            f"{config}")
        raise ValueError(f"wrong resource type: {config}")

    print(config)

    filename: str = config["filename"]
    chain_file: TextIO = resource.open_raw_file(
        filename, "rb", uncompress=True)

    result = LiftoverChain(config, chain_file)
    return result
