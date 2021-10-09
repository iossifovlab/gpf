from .repository import register_genomic_resource_type
from .repository_factory import register_real_genomic_resource_repository_type
from .repository_factory import build_genomic_resource_repository
from .repository import GenomicResource

from .positionscore import GenomicResourcePositionScores
from .positionscore import GenomicResourceRefGenome
from .gene_models_resource import GeneModelsResource

from .embeded_repository import GenomicResourceEmbededRepo
from .url_repository import GenomicResourceURLRepo
from .dir_repository import GenomicResourceDirRepo

__all__ = ["build_genomic_resource_repository", "GenomicResource",
           "GenomicResourcePositionScores", "GenomicResourceGeneModels"]

register_genomic_resource_type("PositionScore", GenomicResourcePositionScores)
register_genomic_resource_type("RefGenome", GenomicResourceRefGenome)
register_genomic_resource_type("GeneModels", GeneModelsResource)

register_real_genomic_resource_repository_type(
    "url", GenomicResourceURLRepo)
register_real_genomic_resource_repository_type(
    "directory", GenomicResourceDirRepo)
register_real_genomic_resource_repository_type(
    "embeded", GenomicResourceEmbededRepo)
