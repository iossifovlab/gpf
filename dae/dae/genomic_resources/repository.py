import os
import yaml
from typing import List, Dict
from glob import glob
from subprocess import call
import pathlib
import logging

import requests
import urllib.request
from urllib.parse import urlparse, urljoin

from dae.annotation.tools.annotator_config import AnnotationConfigParser

from dae.genomic_resources.resources import ParentsScoreTuple, \
    GenomicResourceBase, GenomicResource, GenomicResourceGroup
from dae.genomic_resources.manifest import Manifest
from dae.genomic_resources.http_file import HTTPFile
from dae.genomic_resources.utils import resource_type_to_class

logger = logging.getLogger(__name__)


def create_genomic_resources_repository(repository_path):
    pass


def walk_genomic_resources_repository(repository_path):
    for root, dirs, files in os.walk(repository_path):
        print("root:", root)
        print("dirs:", dirs)
        print("files:", files)

        print(root, "consumes", end=" ")
        print(sum(
            os.path.getsize(os.path.join(root, name)) 
            for name in files), end=" ")
        print("bytes in", len(files), "non-directory files")

class GenomicResourcesRepo:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self, gsd_id: str, repo_content):
        self.gsd_id = gsd_id

        self.resources: Dict[str, GenomicResourceBase] = dict()

        self._load_genomic_resources(repo_content)

    @staticmethod
    def create_genomic_resource_repository(repository_path):
        logger.info("Gathering genomic resources")

        root_path = pathlib.Path(repository_path).absolute()
        conf_files = glob(
            os.path.join(root_path, "**", "genomic_resource.yaml"),
            recursive=True
        )
        root_url = root_path.as_uri()
        root = GenomicResourceGroup("root", root_url)
        print("conf_files:", conf_files)
        for conf_path in conf_files:
            score_path = conf_path[len(root_path.as_posix()):]
            score_path = score_path.strip('/').split('/')
            assert len(score_path) >= 1, score_path
            curr_group = root
            curr_path = root_path.as_posix()
            group_name = ""
            print("score_path:", score_path)
            for group in score_path[:-2]:
                group_name += f"/{group}"
                curr_path = f"{root_path.as_posix()}/{group_name}"
                group_name = group_name.strip("/")
                print("group_name:", group_name)
                if group_name not in curr_group.children:
                    url = pathlib.Path(curr_path).absolute().as_uri()
                    print("curr_path:", curr_path)
                    resource = GenomicResourceGroup(group_name, url)
                    curr_group.add_child(resource)
                curr_group = curr_group.children[group_name]
                print("curr_group:", curr_group)

            curr_path += f"/{score_path[-2]}"
            print("curr_path:", curr_path)

            config = AnnotationConfigParser.load_annotation_config(
                conf_path
            )
            score_url = pathlib.Path(curr_path).absolute().as_uri()
            score = GenomicResource(config, score_url, None, None)
            curr_group.add_child(score)

        repo_content = dict()

        logger.info("Writing resources to CONTENT metadata")

        def add_resource_to_content_dict(resource, section):
            section["id"] = resource.get_id()
            if isinstance(resource, GenomicResourceGroup):
                section["type"] = "group"
                section["children"] = []
                for child in resource.get_children():
                    child_section = dict()
                    add_resource_to_content_dict(child, child_section)
                    section["children"].append(child_section)
            else:
                section["type"] = "resource"

        add_resource_to_content_dict(root, repo_content)

        content_filepath = os.path.join(root_path.as_posix(), "CONTENT.yaml")

        with open(content_filepath, "w") as out:
            yaml.dump(
                repo_content, out, default_flow_style=False, sort_keys=False
            )

        logger.info("Generating MANIFEST files")

        for resource in root.get_resources():
            cwd = urlparse(resource.get_url()).path
            print("manifest in:", cwd)

            print(resource.get_url())
            call(
                "find . -type f \\( ! -iname \"MANIFEST\" \\)  "
                "-exec sha256sum {} \\; | sed \"s|\\s\\./||\""
                "> MANIFEST",
                cwd=cwd,
                shell=True
            )

    def _load_genomic_resources(self, content_section, parent=None):
        if content_section is None:
            return
        if content_section["type"] == "group":
            if parent is None:
                url = self._url
            else:
                url = os.path.join(self._url, content_section["id"])
            resource = GenomicResourceGroup(
                content_section["id"],
                url
            )
            if parent is None:
                self.top_level_group = resource
            else:
                parent.add_child(resource)
            self.resources[resource.get_id()] = resource
            for child in content_section["children"]:
                self._load_genomic_resources(child, resource)
        else:
            assert parent is not None
            url = os.path.join(self._url, content_section["id"])
            manifest_uri = os.path.join(url, "MANIFEST")
            manifest = Manifest(self._stream_resource_file_internal(
                manifest_uri, None, None
            ))
            config_uri = os.path.join(
                url, "genomic_resource.yaml"
            )
            config = AnnotationConfigParser.load_annotation_config_from_stream(
                self._stream_resource_file_internal(config_uri, None, None)
            )
            resource_class = resource_type_to_class(config["resource_type"])
            resource = resource_class(
                config,
                url,
                manifest,
                self
            )
            self.resources[resource.get_id()] = resource
            parent.add_child(resource)

    def reload(self):
        raise NotImplementedError

    def get_name(self):
        return self.gsd_id

    def get_url(self):
        return self._url

    def get_resources_root(self):
        return self.top_level_group

    def get_resource(self, resource_id: str) -> GenomicResourceBase:
        return self.resources.get(resource_id)

    def get_resource_children(
            self, resource_id: str) -> List[GenomicResourceBase]:
        resource = self.resources.get(resource_id)
        if resource is None:
            return None
        return resource.get_children()

    def _stream_resource_file_internal(self, file_uri, offset, size):
        raise NotImplementedError

    def stream_resource_file(
            self, resource_id: str, filename: str,
            offset: int = None, size: int = None):
        """
        Returns a file object related to a given genomic score.
        """
        resource = self.get_resource(resource_id)
        file_url = os.path.join(resource.get_url(), filename)
        return self._stream_resource_file_internal(file_url, offset, size)

    def get_genomic_score(self, genomic_score_id: str) -> ParentsScoreTuple:
        return self.top_level_group.get_genomic_score(genomic_score_id)

    @property
    def genomic_scores(self) -> List[ParentsScoreTuple]:
        """
        Returns all constituent genomic scores of this repository.
        """
        return self.top_level_group.resource_children()

    def open_file(self, resource_id: str, filename: str):
        raise NotImplementedError


class FSGenomicResourcesRepo(GenomicResourcesRepo):
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, gsd_id: str, path: str):
        repo_content = None
        content_path = os.path.join(path, "CONTENT.yaml")
        if os.path.exists(content_path):
            with open(content_path, "r") as content:
                repo_content = yaml.safe_load(content)
        self._url = pathlib.Path(path).absolute().as_uri()
        super().__init__(gsd_id, repo_content)

    def _add_genomic_resource(self, resource, parent):
        parent.children[resource.get_id()] = resource
        self.resources[resource.get_id()] = resource

    def reload(self):
        path = urlparse(self._url).path
        self.__init__(self.gsd_id, path)

    def _stream_resource_file_internal(self, file_uri, offset, size):
        # TODO Implement progress bar and interruptible download
        abspath = urlparse(file_uri).path
        with open(abspath, "rb") as f:
            yield f.read(8192)

    def open_file(self, resource_id: str, filename: str):
        resource = self.get_resource(resource_id)
        file_url = os.path.join(resource.get_url(), filename)
        filepath = urlparse(file_url).path
        return open(filepath, "r")


class HTTPGenomicResourcesRepo(GenomicResourcesRepo):
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
        self._url = url
        opener = urllib.request.FancyURLopener({})
        content_url = urljoin(
            self._url,
            "CONTENT.yaml"
        )
        print(content_url)
        repo_content = yaml.safe_load(
            opener.open(content_url).read().decode("utf-8")
        )
        super().__init__(gsd_id, repo_content)

    def reload(self):
        self.__init__(self.gsd_id, self._url)

    def _stream_resource_file_internal(self, file_uri, offset, size):
        # TODO Implement progress bar and interruptible download
        print("Providing: ", file_uri)
        with requests.get(file_uri, stream=True) as response:
            assert response.status_code == requests.codes.ok, \
                response.status_code
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

    def open_file(self, resource_id: str, filename: str):
        resource = self.get_resource(resource_id)
        file_url = os.path.join(resource.get_url(), filename)
        return HTTPFile(file_url)
