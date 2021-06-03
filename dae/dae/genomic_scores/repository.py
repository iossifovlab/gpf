import os
import yaml
from glob import glob
from typing import List

import urllib.request
from bs4 import BeautifulSoup

from dae.genomic_scores.scores import GenomicScore, GenomicScoreGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema


class BaseGenomicScoreRepository:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self, gsd_id: str, top_level_id: str):
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

    def __init__(self, gsd_id: str, path: str):
        super().__init__(gsd_id, path.rstrip('/').split('/')[-1])
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
                GPFConfigParser.load_config(conf_path, genomic_score_schema)
            )

    def cache(self, genomic_score_id: str):
        raise NotImplementedError()


class HTTPGenomicScoreRepository(BaseGenomicScoreRepository):
    """
    A genomic score repository on a local or remote filesystem.
    """

    IGNORE_LIST = [
        "Name",
        "Last modified",
        "Size",
        "Description",
        "Parent Directory",
    ]

    def __init__(self, gsd_id: str, url: str):
        super().__init__(gsd_id, url.rstrip('/').split('/')[-1])
        self.url = url
        self.top_level_group.children = self._collect_gsd_children(self.url)

    @staticmethod
    def _collect_gsd_children(root_url: str):
        opener = urllib.request.FancyURLopener({})
        content = opener.open(root_url).read()
        soup = BeautifulSoup(content, 'html.parser')

        links = list(filter(
            lambda el: el.text not in HTTPGenomicScoreRepository.IGNORE_LIST,
            soup.find_all("a")
        ))

        conf_file_tag = next(
            filter(lambda link: ".yaml" in link.text, links), None
        )

        children = dict()
        if conf_file_tag is not None:
            conf_url = conf_file_tag.attrs["href"]
            raw_conf = yaml.safe_load(opener.open(
                os.path.join(root_url, conf_url)
            ).read().decode("utf-8"))
            # FIXME temporarily disabled until remote has proper confs
            # children[root_url] = GenomicScore(
            #     GPFConfigParser.process_config(raw_conf, genomic_score_schema)
            # )
            children[root_url] = raw_conf
        else:
            subdirectories = filter(
                lambda entry: entry[-1] == '/',
                map(lambda link: link.attrs["href"], links)
            )
            for subdir in subdirectories:
                # FIXME genomic score group's id is saved with a trailing '/'
                full_url = os.path.join(root_url, subdir)
                genomic_score_group = GenomicScoreGroup(subdir)
                genomic_score_group.children = \
                    HTTPGenomicScoreRepository._collect_gsd_children(full_url)
                children[subdir] = genomic_score_group

        return children

    def cache(self, genomic_score_id: str):
        raise NotImplementedError()
