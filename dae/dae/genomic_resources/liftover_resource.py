from __future__ import annotations

from dae.genomic_resources.repository import GenomicResourceRealRepo
from dae.genomic_resources import GenomicResource
import logging

from pyliftover import LiftOver

logger = logging.getLogger(__name__)


class LiftoverChainResource(GenomicResource):

    def __init__(self, resourceId: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(resourceId, version, repo, config)
        self.file = config["file"]
        self.chrom_variant_coordinates = config.get(
            'chrom_prefix.variant_coordinates', None)
        self.chrom_target_coordinates = config.get(
            'chrom_prefix.target_coordinates', None)

    @classmethod
    def get_resource_type(clazz):
        return "liftover_chain"

    def open(self) -> LiftoverChainResource:
        file = self.get_config()["file"]

        self.chain_file = self.open_raw_file(file, "rb", uncompress=True)
        self.liftover = LiftOver(self.chain_file)
        return self

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
