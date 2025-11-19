from __future__ import annotations

import logging
from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dae.genomic_resources.gene_models.gene_models import GeneModels
    from dae.genomic_resources.repository import (
        GenomicResource,
        GenomicResourceRepo,
    )

logger = logging.getLogger(__name__)

_INMEMORY_CACHE: dict[tuple[str, str], GeneModels] = {}
_INMEMORY_CACHE_LOCK = Lock()


def build_gene_models_from_file(
    file_name: str,
    file_format: str | None = None,
    gene_mapping_file_name: str | None = None,
    chrom_mapping_file_name: str | None = None,
) -> GeneModels:
    """Load gene models from local filesystem."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.fsspec_protocol import (
        build_local_resource,
    )

    from .gene_models import GeneModels
    cache_id = (file_name, "file:///.")

    with _INMEMORY_CACHE_LOCK:
        if cache_id in _INMEMORY_CACHE:
            return _INMEMORY_CACHE[cache_id]

        config: dict[str, Any] = {
            "type": "gene_models",
            "filename": file_name,
        }
        if file_format:
            config["format"] = file_format
        if gene_mapping_file_name:
            config["gene_mapping"] = gene_mapping_file_name
        if chrom_mapping_file_name is not None:
            config["chrom_mapping"] = {
                "filename": chrom_mapping_file_name,
            }

        res = build_local_resource(".", config)

        gene_models = GeneModels(res)
        _INMEMORY_CACHE[cache_id] = gene_models
        return gene_models


def build_gene_models_from_resource(
    resource: GenomicResource | None,
) -> GeneModels:
    """Load gene models from a genomic resource."""
    # pylint: disable=import-outside-toplevel
    from .gene_models import GeneModels

    if resource is None:
        raise ValueError(f"missing resource {resource}")

    if resource.get_type() != "gene_models":
        logger.error(
            "trying to open a resource %s of type "
            "%s as gene models", resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    cache_id = (resource.get_full_id(), resource.get_repo_url())
    with _INMEMORY_CACHE_LOCK:
        if cache_id in _INMEMORY_CACHE:
            return _INMEMORY_CACHE[cache_id]

        gene_models = GeneModels(resource)
        _INMEMORY_CACHE[cache_id] = gene_models
        return gene_models


def build_gene_models_from_resource_id(
    resource_id: str, grr: GenomicResourceRepo | None = None,
) -> GeneModels:
    """Load gene models from a genomic resource id."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.repository_factory import (
        build_genomic_resource_repository,
    )
    if grr is None:
        grr = build_genomic_resource_repository()

    return build_gene_models_from_resource(grr.get_resource(resource_id))
