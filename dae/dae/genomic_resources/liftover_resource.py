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
        return "LiftoverChain"

    def open(self):
        file = self.get_config()["file"]

        self.chain_file = self.open_raw_file(file, "rb", uncompress=True)
        self.liftover = LiftOver(self.chain_file)

    def close(self):
        pass

    def convert_coordinate(self, chrom, pos):
        variant_coordinates = self.chrom_variant_coordinates
        if variant_coordinates:
            if variant_coordinates.del_prefix:
                del_prefix = variant_coordinates.del_prefix
                if chrom.startswith(del_prefix):
                    chrom = chrom.lstrip(del_prefix)
            elif variant_coordinates.add_prefix:
                add_prefix = variant_coordinates.add_prefix
                chrom = f"{add_prefix}{chrom}"

        lo_coordinates = self.liftover.convert_coordinate(chrom, pos - 1)

        if not lo_coordinates:
            return None
        if len(lo_coordinates) > 1:
            logger.info(
                f"liftover_variant: liftover returns more than one target "
                f"position: {lo_coordinates}")

        coordinates = lo_coordinates[0]

        target_coordinates = self.chrom_target_coordinates
        if target_coordinates:
            new_chrom = None
            if target_coordinates.del_prefix:
                del_prefix = target_coordinates.del_prefix
                if chrom.startswith(del_prefix):
                    new_chrom = coordinates[0].lstrip(
                        del_prefix
                    )
            elif target_coordinates.add_prefix:
                add_prefix = target_coordinates.add_prefix
                new_chrom = f"{add_prefix}{coordinates[0]}"

            if new_chrom is not None:
                coordinates = (
                    new_chrom,
                    coordinates[1],
                    coordinates[2],
                    coordinates[3],
                )

        return coordinates
