from copy import deepcopy

from dae.genomic_resources.resources import GenomicResource
from dae.configuration.schemas.genomic_resources_database import \
    gene_models_schema


class GeneModelsResource(GenomicResource):

    def __init__(self, config, repo):
        super().__init__(config, repo)

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(gene_models_schema)
        return schema
