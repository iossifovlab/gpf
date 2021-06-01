from typing import List

from dae.genomic_scores.scores import GenomicScore, GenomicScoreGroup


class BaseGenomicScoreRepository:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    @property
    def is_local(self) -> bool:
        raise NotImplementedError()

    @property
    def genomic_scores(self) -> List[GenomicScore]:
        """
        Returns all constituent genomic scores of this repository.
        """
        raise NotImplementedError()

    @property
    def top_level(self) -> GenomicScoreGroup:
        """
        Return the 'root' genomic score group of this repository.
        """
        raise NotImplementedError()

    def get_genomic_score(self, genomic_score_id: str) -> GenomicScore:
        raise NotImplementedError()

    def cache(self, genomic_score_id: str):
        """
        Save a remote genomic score to the local genomic score storage.
        """
        raise NotImplementedError()


class FilesystemGenomicScoreRepository:
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, path: str):
        self.path = path

    @property
    def is_local(self) -> bool:
        return True

    @property
    def genomic_scores(self) -> List[GenomicScore]:
        """
        Returns all constituent genomic scores of this repository.
        """
        raise NotImplementedError()

    @property
    def top_level(self) -> GenomicScoreGroup:
        """
        Return the 'root' genomic score group of this repository.
        """
        raise NotImplementedError()

    def get_genomic_score(self, genomic_score_id: str) -> GenomicScore:
        raise NotImplementedError()

    def cache(self, genomic_score_id: str):
        """
        Save a remote genomic score to the local genomic score storage.
        """
        raise NotImplementedError()
