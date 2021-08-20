from copy import deepcopy

# from dae.genome.gene_models import GeneModelsBase
from dae.genomic_resources.resources import GenomicResource
from dae.configuration.schemas.genomic_resources_database import \
    gene_models_schema


class GeneModelsResource(GenomicResource):  # , GeneModelsBase):

    def __init__(self, config, repo):
        GenomicResource.__init__(self, config, repo)
        # GeneModelsBase.__init__(self, config["id"])

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(gene_models_schema)
        return schema

    def open(self):
        filename = self.get_config().filename
        fileformat = self.get_config().format

        with self.open_file(filename) as infile:
            pass
