import logging

from dae.genomic_resources.gene_models import GeneModels
from .repository import GenomicResource

logger = logging.getLogger(__name__)


def load_gene_models_from_resource(resource: GenomicResource) -> GeneModels:

    if resource is None:
        raise ValueError(f"missing resource {resource}")

    if resource.get_type() != "gene_models":
        logger.error(
            f"trying to open a resource {resource.resource_id_id} of type "
            f"{resource.get_type()} as gene models")
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    filename = resource.get_config()["filename"]
    fileformat = resource.get_config().get("format", None)
    gene_mapping_filename = resource.get_config().get("gene_mapping", None)
    logger.debug(f"loading gene models {filename} ({fileformat})")

    gm = GeneModels(('resource', resource.repo.repo_id, resource.resource_id))
    with resource.open_raw_file(
            filename, mode='rt',
            uncompress=True, seekable=True) as infile:
        if gene_mapping_filename is not None:
            with resource.open_raw_file(
                    gene_mapping_filename,
                    "rt", uncompress=True) as gene_mapping:
                logger.debug(
                    f"loading gene mapping from {gene_mapping_filename}")
                gm.load(infile, fileformat, gene_mapping)
        else:
            gm.load(infile, fileformat)
    return gm
