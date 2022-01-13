import logging

from dae.genomic_resources.gene_models import GeneModels
from .repository import GenomicResource
from .repository import GenomicResourceRealRepo

logger = logging.getLogger(__name__)


class GeneModelsResource(GenomicResource):

    def __init__(self, resourceId: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        GenomicResource.__init__(self, resourceId, version, repo, config)
        # GeneModels.__init__(self, resourceId)

    @staticmethod
    def get_resource_type():
        return "gene_models"

    def open(self) -> GeneModels:
        filename = self.get_config()["filename"]
        fileformat = self.get_config().get("format", None)
        gene_mapping_filename = self.get_config().get("gene_mapping", None)
        logger.debug(f"loading gene models {filename} ({fileformat})")

        gm = GeneModels(('resource', self.repo.repo_id, self.resource_id))
        with self.open_raw_file(filename, mode='rt',
                                uncompress=True, seekable=True) as infile:
            if gene_mapping_filename is not None:
                with self.open_raw_file(gene_mapping_filename,
                                        "rt", uncompress=True) as gene_mapping:
                    logger.debug(
                        f"loading gene mapping from {gene_mapping_filename}")
                    gm.load(infile, fileformat, gene_mapping)
            else:
                gm.load(infile, fileformat)
        return gm
    '''
        gene_mapping = None
        if gene_mapping_filename is not None:
            with self.open_raw_file(gene_mapping_filename,
                                    "rt", uncompress=True) as infile:
                logger.debug(
                    f"loading gene mapping from {gene_mapping_filename}")
                gene_mapping = self._gene_mapping(infile)
                logger.debug(
                    f"loaded {len(gene_mapping)} gene mappnigs.")

        with self.open_raw_file(
                filename, mode='rb',
                uncompress=True, seekable=True) as infile:
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
            status = parser(infile, gene_mapping=gene_mapping)
            if not status:
                msg = f"failed parsing gene model {self.get_id()}"
                logger.error(msg)
                raise ValueError(msg)
        return self
    '''
