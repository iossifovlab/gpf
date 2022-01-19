from .repository import register_genomic_resource_type
from .repository_factory import register_real_genomic_resource_repository_type
from .repository_factory import build_genomic_resource_repository
from .repository import GenomicResource

from .reference_genome_resource import ReferenceGenomeResource
from .gene_models_resource import GeneModelsResource
from .liftover_resource import LiftoverChainResource
from .score_resources import PositionScoreResource, NPScoreResource, \
    AlleleScoreResource

from .embeded_repository import GenomicResourceEmbededRepo
from .url_repository import GenomicResourceURLRepo
from .dir_repository import GenomicResourceDirRepo

__all__ = [
    "build_genomic_resource_repository", "GenomicResource",
    "ReferenceGenomeResource", "GeneModelsResource",
    "LiftoverChainResource",
    "PositionScoreResource", "NPScoreResource", "AlleleScoreResource",
]


register_genomic_resource_type(GenomicResource, "Basic")
register_genomic_resource_type(ReferenceGenomeResource, "genome")
register_genomic_resource_type(LiftoverChainResource, "liftover_chain")
register_genomic_resource_type(PositionScoreResource, "position_score")
register_genomic_resource_type(NPScoreResource, "np_score")
register_genomic_resource_type(AlleleScoreResource, "allele_score")


register_real_genomic_resource_repository_type(
    "url", GenomicResourceURLRepo)
register_real_genomic_resource_repository_type(
    "directory", GenomicResourceDirRepo)
register_real_genomic_resource_repository_type(
    "embeded", GenomicResourceEmbededRepo)


_PLUGINS_LOADED = False


def _load_plugins():
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return

    from importlib_metadata import entry_points
    discovered_plugins = entry_points(group='dae.genomic_resources.plugins')
    for dp in discovered_plugins:
        dp.load()()
    _PLUGINS_LOADED = True
    return None


_load_plugins()
