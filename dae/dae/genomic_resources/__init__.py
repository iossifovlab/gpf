from .repository import register_genomic_resource_type
from .repository_factory import register_real_genomic_resource_repository_type
from .repository_factory import build_genomic_resource_repository
from .repository import GenomicResource

from .reference_genome_resource import GenomicSequenceResource
from .gene_models_resource import GeneModelsResource
from .liftover_resource import LiftoverChainResource
from .score_resources import PositionScoreResource, NPScoreResource, \
    AlleleScoreResource

from .embeded_repository import GenomicResourceEmbededRepo
from .url_repository import GenomicResourceURLRepo
from .dir_repository import GenomicResourceDirRepo

__all__ = [
    "build_genomic_resource_repository", "GenomicResource",
    "GenomicSequenceResource", "GeneModelsResource",
    "LiftoverChainResource",
    "PositionScoreResource", "NPScoreResource", "AlleleScoreResource",
]


register_genomic_resource_type(GenomicResource)
register_genomic_resource_type(GeneModelsResource)
register_genomic_resource_type(GenomicSequenceResource)
register_genomic_resource_type(LiftoverChainResource)
register_genomic_resource_type(PositionScoreResource)
register_genomic_resource_type(NPScoreResource)
register_genomic_resource_type(AlleleScoreResource)


register_real_genomic_resource_repository_type(
    "url", GenomicResourceURLRepo)
register_real_genomic_resource_repository_type(
    "directory", GenomicResourceDirRepo)
register_real_genomic_resource_repository_type(
    "embeded", GenomicResourceEmbededRepo)
