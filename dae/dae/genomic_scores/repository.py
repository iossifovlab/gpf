from typing import List

from dae.genomic_scores.scores import GenomicScore, GenomicScoreGroup


class BaseGenomicScoreRepository:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self):
        self.top_level_group: GenomicScoreGroup = GenomicScoreGroup()

    @property
    def is_local(self) -> bool:
        raise NotImplementedError()

    @property
    def genomic_scores(self) -> List[GenomicScore]:
        """
        Returns all constituent genomic scores of this repository.
        """
        return self.top_level_group.score_children

    def get_genomic_score(self, genomic_score_id: str) -> GenomicScore:
        return self.top_level_group.get_genomic_score(genomic_score_id)

    def cache(self, genomic_score_id: str):
        """
        Save a remote genomic score to the local genomic score storage.
        """
        raise NotImplementedError()


class FilesystemGenomicScoreRepository(BaseGenomicScoreRepository):
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        # TODO Implement discovery

    @property
    def is_local(self) -> bool:
        return True

    def cache(self, genomic_score_id: str):
        raise NotImplementedError()


class HTTPGenomicScoreRepository(BaseGenomicScoreRepository):
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        # TODO Implement discovery

    @property
    def is_local(self) -> bool:
        return False

    def cache(self, genomic_score_id: str):
        raise NotImplementedError()
