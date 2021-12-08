import logging


from dae.utils.regions import Region
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.repository import GenomicResourceRealRepo


logger = logging.getLogger(__name__)


class GenomicSequenceResource(GenomicResource, ReferenceGenome):

    def __init__(self, resourceId: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        GenomicResource.__init__(self, resourceId, version, repo, config)
        ReferenceGenome.__init__(self)
        self.PARS = self._parse_PARS(config)

    @classmethod
    def get_resource_type(clazz):
        return "genome"

    @staticmethod
    def _parse_PARS(config):
        if "PARS" not in config:
            return None

        assert config["PARS"]["X"] is not None
        regions_x = [
            Region.from_str(region) for region in config["PARS"]["X"]
        ]
        chrom_x = regions_x[0].chrom

        result = {
            chrom_x: regions_x
        }

        if config["PARS"]["Y"] is not None:
            regions_y = [
                Region.from_str(region) for region in config["PARS"]["Y"]
            ]
            chrom_y = regions_y[0].chrom
            result[chrom_y] = regions_y
        return result

    def open(self):
        file_name = self.get_config()["filename"]

        index_file_name = self.get_config().get("index_file",
                                                file_name + ".fai")
        index_content = self.get_file_str_content(index_file_name)
        self._load_genome_index(index_content)
        self._sequence = self.open_raw_file(
            file_name, "rb", uncompress=False, seekable=True)
