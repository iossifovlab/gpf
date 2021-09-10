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
        lo_coordinates = self.liftover.convert_coordinate(chrom, pos - 1)

        if not lo_coordinates:
            return None
        if len(lo_coordinates) > 1:
            logger.info(
                f"liftover_variant: liftover returns more than one target "
                f"position: {lo_coordinates}")

        return lo_coordinates[0]

    @classmethod
    def get_config_schema(cls):
        return genomic_score_schema
