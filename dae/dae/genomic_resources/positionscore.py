from .repository import GenomicResource
from .repository import GenomicResourceRealRepo


class GenomicResourcePositionScores(GenomicResource):
    def __init__(self, id: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(id, version, repo, config)


class GenomicResourceRefGenome(GenomicResource):
    def __init__(self, id: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(id, version, repo, config)


class GenomicResourceGeneModels(GenomicResource):
    def __init__(self, id: str, version: tuple,
                 repo: GenomicResourceRealRepo,
                 config=None):
        super().__init__(id, version, repo, config)
