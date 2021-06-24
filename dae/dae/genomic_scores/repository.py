import os
import yaml
from glob import glob
from typing import List, Dict

import requests
import urllib.request
from bs4 import BeautifulSoup

from dae.genomic_scores.scores import ParentsScoreTuple, GenomicScore, \
    GenomicScoreGroup


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
            score = GenomicScore(conf_path)
            curr_group.children[score.id] = score
            self.config_files[score.id] = score_path[-1]

    def reload(self):
        self.__init__(self.gsd_id, self.path)

    def provide_file(self, genomic_score_id: str, filename: str):
        # TODO Implement progress bar and interruptible download
        parents, _ = self.get_genomic_score(genomic_score_id)
        abspath = os.path.join(
            self.path, *list(map(lambda p: p.id, parents[1:]))
        )
        with open(os.path.join(abspath, filename), "rb") as f:
            yield f.read(8192)


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
        # FIXME
        # This method uses a couple of hacks in order to read an
        # outdated remote GS repository, it should be cleaned up
        # when the remote repo is updated

        opener = urllib.request.FancyURLopener({})
        content = opener.open(root_url).read()
        soup = BeautifulSoup(content, 'html.parser')

        links = list(filter(
            lambda el: el.text not in HTTPGenomicScoreRepository.IGNORE_LIST,
            soup.find_all("a")
        ))

        # FIXME change to ".gs.yaml" when remote repo is updated
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
            # code below should be deleted and replaced with snippet above
            from box import Box
            raw_conf = Box(
                {
                    "id": raw_conf["id"],
                    "filename": raw_conf["score_file"]["filename"],
                    "index_file": raw_conf["index_file"],
                    "config": {"filename": raw_conf["score_file"]["filename"], **raw_conf}
                }
            )
            children[raw_conf.id] = raw_conf
            # FIXME hardcoded gnomad.exomes.yaml for testing purposes
            # self.config_files[raw_conf.id] = score_name
            self.config_files[raw_conf.id] = "gnomad.exomes.yaml"
        else:
            subdirectories = filter(
                lambda entry: entry[-1] == '/',
                map(lambda link: link.attrs["href"], links)
            )
            for subdir in subdirectories:
                # FIXME genomic score group's id is saved with a trailing '/'
                full_url = os.path.join(root_url, subdir)
                genomic_score_group = children.setdefault(
                    subdir, GenomicScoreGroup(subdir)
                )
                genomic_score_group.children = \
                    self._collect_gsd_children(full_url)

        return children

    def reload(self):
        self.__init__(self.gsd_id, self.url)

    def provide_file(self, genomic_score_id: str, filename: str):
        # TODO Implement progress bar and interruptible download
        parents, _ = self.get_genomic_score(genomic_score_id)
        url = os.path.join(
            self.url, *list(map(lambda p: p.id, parents[1:])), filename
        )
        print("Providing: ", url)
        with requests.get(url, stream=True) as response:
            assert response.status_code == requests.codes.ok, \
                response.status_code
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
