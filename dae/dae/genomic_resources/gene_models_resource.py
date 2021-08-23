import logging
from copy import deepcopy

from dae.genome.gene_models import GeneModelsBase
from dae.genomic_resources.resources import GenomicResource
from dae.configuration.schemas.genomic_resources_database import \
    gene_models_schema


logger = logging.getLogger(__name__)


class GeneModelsResource(GenomicResource, GeneModelsBase):

    def __init__(self, config, repo):
        GenomicResource.__init__(self, config, repo)
        GeneModelsBase.__init__(self, config["id"])

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(gene_models_schema)
        return schema

    def open(self):
        filename = self.get_config().filename
        fileformat = self.get_config().format
        gene_mapping_filename = self.get_config().gene_mapping

        logger.debug(f"loading gene models {filename} ({fileformat})")
        gene_mapping = None
        if gene_mapping_filename is not None:
            with self.open_file(gene_mapping_filename) as infile:
                gene_mapping = self._gene_mapping(infile)

        with self.open_file(filename) as infile:
            if fileformat is None:
                fileformat = self._infer_gene_model_parser(infile)
                logger.debug(
                    f"infered gene models file format: {fileformat} "
                    f"for {self.get_id()} gene models")
                if fileformat is None:
                    msg = f"can't infer gene models file format for " \
                        f"gene models: {self.get_id()}..."
                    logger.error(msg)
                    raise ValueError(msg)

            parser = self._get_parser(fileformat)
            if parser is None:
                msg = f"unsupported gene models {self.get_id()} " \
                    f"gene file format: {fileformat}"
                logger.error(msg)
                raise ValueError(msg)

            infile.seek(0)
            self.reset()
            print(parser, type(parser))
            status = parser(infile, gene_mapping=gene_mapping)
            if not status:
                msg = f"failed parsing gene model {self.get_id()}"
                logger.error(msg)
                raise ValueError(msg)
