import os
from glob import glob
from typing import List
from dae.genomic_scores.scores import GenomicScore, GenomicScoreGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema


class BaseGenomicScoreRepository:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self, top_level_id: str):
        self.top_level_group: GenomicScoreGroup = GenomicScoreGroup(
            top_level_id
        )

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
        super().__init__(path.split('/')[-1])
        self.path = path
        self._traverse_gsd_dir(self.path)

    def _traverse_gsd_dir(self, root_path: str):
        conf_files = glob(
            os.path.join(root_path, "**", "*.gs.yaml"), recursive=True
        )
        for conf_path in conf_files:
            score_path = conf_path[len(root_path):]
            score_path_tokens = score_path.split('/')
            assert len(score_path_tokens) >= 2, score_path_tokens
            curr_group = self.top_level_group
            for group in score_path_tokens[:-2]:
                curr_group.children[group] = GenomicScoreGroup(group)
                curr_group = curr_group.children[group]
            curr_group.children[score_path_tokens[-2]] = GenomicScore(
                GPFConfigParser.load_config(score_path, genomic_score_schema)
            )

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

    def cache(self, genomic_score_id: str):
        raise NotImplementedError()
