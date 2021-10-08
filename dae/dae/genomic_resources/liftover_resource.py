import os
import logging
from urllib.parse import urlparse

from pyliftover import LiftOver

from dae.genomic_resources.resources import GenomicResource
from dae.annotation.tools.utils import is_gzip
from dae.configuration.schemas.genomic_resources_database import \
    genomic_score_schema

logger = logging.getLogger(__name__)


class LiftoverChainResource(GenomicResource):
    def open(self):
        assert self._config.filename
        print("================")
        print(self._config.filename)
        if urlparse(self.get_url()).scheme == "file":
            print("LOCAL FILESYSTEM")
            print("LOCAL FILESYSTEM")
            print("LOCAL FILESYSTEM")
            print("LOCAL FILESYSTEM")
            print("LOCAL FILESYSTEM")
            scores_filename = f"{self.get_url()}/{self._config.filename}"
            scores_filename = urlparse(scores_filename).path
            assert os.path.exists(scores_filename), scores_filename
            assert is_gzip(scores_filename)
        self.chain_file = self.open_file(self._config.filename, "rb")
        print(self.chain_file)
        print(type(self.chain_file))
        self.liftover = LiftOver(self.chain_file)

    def close(self):
        pass

    def convert_coordinate(self, chrom, pos):
        variant_coordinates = self._config.chrom_prefix.variant_coordinates
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

        target_coordinates = self._config.chrom_prefix.target_coordinates
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

    @classmethod
    def get_config_schema(cls):
        return genomic_score_schema
