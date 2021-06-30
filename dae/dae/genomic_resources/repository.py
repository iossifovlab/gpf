import os
import yaml
from typing import List, Dict
import pathlib

import requests
import urllib.request
from urllib.parse import urlparse, urljoin

from dae.annotation.tools.annotator_config import AnnotationConfigParser

from dae.genomic_resources.resources import ParentsScoreTuple, \
    GenomicResourceBase, GenomicResource, GenomicResourceGroup
from dae.genomic_resources.manifest import Manifest


class GenomicResourcesRepo:
    """
    Describes a collection of genomic scores and genomic score groups.
    """

    def __init__(self, gsd_id: str, repo_content):
        self.gsd_id = gsd_id

        self.resources: Dict[str, GenomicResourceBase] = dict()

        self._load_genomic_resources(repo_content)

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
            resource = GenomicResource(
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
        file_url = urljoin(resource.get_url(), filename)
        return self._stream_resource_file_internal(file_url, offset, size)

    def get_genomic_score(self, genomic_score_id: str) -> ParentsScoreTuple:
        return self.top_level_group.get_genomic_score(genomic_score_id)

    @property
    def genomic_scores(self) -> List[ParentsScoreTuple]:
        """
        Returns all constituent genomic scores of this repository.
        """
        return self.top_level_group.score_children()


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
        self.__init__(self.gsd_id, self.path)

    def _stream_resource_file_internal(self, file_uri, offset, size):
        # TODO Implement progress bar and interruptible download
        abspath = urlparse(file_uri).path
        with open(abspath, "rb") as f:
            yield f.read(8192)


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
        self.__init__(self.gsd_id, self.url)

    def _stream_resource_file_internal(self, file_uri, offset, size):
        # TODO Implement progress bar and interruptible download
        print("Providing: ", file_uri)
        with requests.get(file_uri, stream=True) as response:
            assert response.status_code == requests.codes.ok, \
                response.status_code
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
