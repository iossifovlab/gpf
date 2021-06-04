import os
import yaml
from glob import glob
from typing import List, Dict

import urllib.request
from bs4 import BeautifulSoup

from dae.genomic_scores.scores import ParentsScoreTuple, GenomicScore, \
    GenomicScoreGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema


class BaseGenomicScoreRepository:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self, gsd_id: str, top_level_id: str):
        self.gsd_id = gsd_id
        self.top_level_group: GenomicScoreGroup = GenomicScoreGroup(
            top_level_id
        )
        self.config_files: Dict[str, str] = dict()

    @property
    def genomic_scores(self) -> List[ParentsScoreTuple]:
        """
        Returns all constituent genomic scores of this repository.
        """
        return self.top_level_group.score_children()

    def reload(self):
        raise NotImplementedError

    def get_genomic_score(self, genomic_score_id: str) -> ParentsScoreTuple:
        return self.top_level_group.get_genomic_score(genomic_score_id)

    def provide_file(self, genomic_score_id: str, filename: str):
        """
        Returns a file object related to a given genomic score.
        """
        raise NotImplementedError


class FilesystemGenomicScoreRepository(BaseGenomicScoreRepository):
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, gsd_id: str, path: str):
        super().__init__(gsd_id, os.path.split(path)[1])
        self.path = path
        self._traverse_gsd_dir(self.path)

    def _traverse_gsd_dir(self, root_path: str):
        conf_files = glob(
            os.path.join(root_path, "**", "*.gs.yaml"), recursive=True
        )
        for conf_path in conf_files:
            score_path = conf_path[len(root_path):].strip('/').split('/')
            assert len(score_path) >= 1, score_path
            curr_group = self.top_level_group
            for group in score_path[:-1]:
                curr_group = curr_group.children.setdefault(
                    group, GenomicScoreGroup(group)
                )
            score = GenomicScore(
                GPFConfigParser.load_config(conf_path, genomic_score_schema)
            )
            curr_group.children[score.id] = score
            self.config_files[score.id] = score_path[-1]

    def reload(self):
        self.__init__(self.gsd_id, self.path)

    def provide_file(self, genomic_score_id: str, filename: str):
        parents, _ = self.get_genomic_score(genomic_score_id)
        abspath = os.path.join(
            self.path, *list(map(lambda p: p.id, parents[1:]))
        )
        return open(os.path.join(abspath, filename), "rb")


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

    def _collect_gsd_children(self, root_url: str):
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
            score_name = conf_file_tag.attrs["href"]
            full_conf_url = os.path.join(root_url, score_name)
            raw_conf = yaml.safe_load(
                opener.open(full_conf_url).read().decode("utf-8")
            )
            # FIXME temporarily disabled until remote has proper confs
            # children[root_url] = GenomicScore(
            #     GPFConfigParser.process_config(raw_conf, genomic_score_schema)
            # )
            children[score_name] = raw_conf
            self.config_files[score_name] = full_conf_url
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
