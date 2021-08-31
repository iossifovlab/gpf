import logging

from copy import deepcopy

from dae.utils.regions import Region
from dae.genome.genome_access import GenomicSequenceBase
from dae.genomic_resources.resources import GenomicResource

from dae.configuration.schemas.genomic_resources_database import \
    genomic_sequence_schema

logger = logging.getLogger(__name__)


class GenomicSequenceResource(GenomicResource, GenomicSequenceBase):

    def __init__(self, config, repo):
        GenomicResource.__init__(self, config, repo)
        GenomicSequenceBase.__init__(self)
        self.PARS = self._parse_PARS(config)

    @staticmethod
    def _parse_PARS(config):
        assert config.PARS.X is not None
        regions_x = [
            Region.from_str(region) for region in config.PARS.X
        ]
        chrom_x = regions_x[0].chrom

        result = {
            chrom_x: regions_x
        }

        if config.PARS.Y is not None:
            regions_y = [
                Region.from_str(region) for region in config.PARS.Y
            ]
            chrom_y = regions_y[0].chrom
            result[chrom_y] = regions_y
        return result

    def open(self):
        index_filename = self.get_config().index_file.filename
        with self.open_file(index_filename) as index_file:
            content = index_file.read()
            print("content:", content)
            self._load_genome_index(content)
        self._sequence = self.open_file(self.get_config().filename)

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(genomic_sequence_schema)
        return schema
