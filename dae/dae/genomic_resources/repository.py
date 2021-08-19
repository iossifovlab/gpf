import os
import yaml
from typing import Dict
from glob import glob
from subprocess import call
import pathlib
import logging

import requests
from urllib.parse import urlparse

from dae.genomic_resources.resources_config import ResourcesConfigParser

from dae.genomic_resources.resources import \
    GenomicResourceBase, GenomicResource, GenomicResourceGroup
from dae.genomic_resources.http_file import HTTPFile
from dae.genomic_resources.utils import resource_type_to_class

logger = logging.getLogger(__name__)


def _create_genomic_resources_hierarchy(repo, parents_resource_iterator):
    root_group = GenomicResourceGroup("", repo=repo)

    for parents, child in parents_resource_iterator:
        group_id = ""
        current_group = root_group
        for group_part in parents:
            group_id = f"{group_id}/{group_part}" if group_id else group_part

            group = current_group.get_resource(group_id, deep=False)
            if group is None:
                group = GenomicResourceGroup(group_id, repo=repo)
                current_group.add_child(group)
            assert isinstance(group, GenomicResourceGroup)

            current_group = group

        resource_id = f"{group_id}/{child[0]}"
        assert current_group.get_resource(resource_id, deep=False) is None

        child = repo.create_resource(resource_id, child[1])
        current_group.add_child(child)

    return root_group


def _walk_genomic_resources_repository(repository_path):
    root_path = pathlib.Path(repository_path).absolute()
    root_dirname = str(root_path)
    resource_files = glob(
        os.path.join(root_path, "**", "genomic_resource.yaml"),
        recursive=True
    )

    for resource_file in resource_files:
        assert resource_file.startswith(root_dirname)
        resource_path = resource_file[len(root_dirname) + 1:]
        parts = resource_path.split(os.path.sep)
        assert len(parts) >= 2

        parents = parts[:-2]
        child = parts[-2:]
        assert len(child) == 2
        child[1] = resource_file
        yield tuple(parents), tuple(child)


def _walk_genomic_repository_content(repo, content, parents=None):
    if parents is None:
        parents = []

    id_part = content["id"].split("/")[-1]

    if content["type"] == "resource":
        path = os.path.join(*parents, id_part, "genomic_resource.yaml")
        url = os.path.join(repo.get_url(), path)

        yield tuple(parents), (id_part, url)
    else:
        assert content["type"] == "group"
        for child in content["children"]:
            child_parents = parents[:]
            if id_part:
                child_parents.append(id_part)
            yield from _walk_genomic_repository_content(
                repo, child, child_parents)


def _create_resource_content_dict(resource: GenomicResourceBase):
    section = dict()
    section["id"] = resource.get_id()
    if isinstance(resource, GenomicResourceGroup):
        section["type"] = "group"
        section["children"] = []
        for child in resource.get_children():
            child_section = _create_resource_content_dict(child)
            section["children"].append(child_section)
    else:
        section["type"] = "resource"
    return section


def create_fs_genomic_resource_repository(repository_id, repository_path):
    repo = FSGenomicResourcesRepo(repository_id, repository_path)

    # walk filesystem for genomic resources
    root_group = _create_genomic_resources_hierarchy(
        repo,
        _walk_genomic_resources_repository(repository_path))
    assert root_group is not None

    repo.set_root(root_group)
    repo.build_repository_content()

    for resource in root_group.get_genomic_resources():
        repo.build_resource_manifest(resource.get_id())

    return repo


class GenomicResourcesRepo:
    """
    Represents a collection of genomic resources and genomic resource groups
    accessible through a specified protocol.

    At the moment the supported protocols are:
    * filesystem
    * HTTP protocol
    """

    def __init__(self, gsd_id: str, path: str):
        self.gsd_id = gsd_id
        self.path = path
        self._url = path

        self.resources: Dict[str, GenomicResource] = dict()
        self.root_group = None

    def _load_repository_content(self):
        logger.info(f"loading repository content for {self._url}")
        content_url = "/".join(
            [self.get_url(), "CONTENT.yaml"]
        )
        logger.info(f"loading from {content_url}")
        file_contents = b""
        for chunk_raw in self._stream_resource_file_internal(
                content_url, None, None):
            file_contents += chunk_raw
        return yaml.safe_load(file_contents.decode("utf-8"))

    def set_root(self, root_group):
        self.root_group = root_group
        for resource in self.root_group.get_genomic_resources():
            self.resources[resource.get_id()] = resource

    def get_path(self):
        return self.path

    def load(self):
        repo_content = self._load_repository_content()
        root_group = _create_genomic_resources_hierarchy(
            self,
            _walk_genomic_repository_content(self, repo_content)
        )
        assert root_group is not None
        self.set_root(root_group)

    def reload(self):
        self.resources: Dict[str, GenomicResource] = dict()
        self.root_group = None
        self.load()

    def create_resource(self, resource_id, config_path):
        config = ResourcesConfigParser.load_resource_config_from_stream(
            self._stream_resource_file_internal(config_path, None, None)
        )
        assert config["id"] == resource_id
        resource_class = resource_type_to_class(config["resource_type"])
        resource = resource_class(config, repo=self)
        return resource

    def get_name(self):
        return self.gsd_id

    def get_url(self):
        return self._url

    def get_resource(self, resource_id: str) -> GenomicResource:
        return self.resources.get(resource_id)

    def _stream_resource_file_internal(self, file_uri, offset, size):
        raise NotImplementedError

    def stream_resource_file(
            self, resource_id: str, filename: str,
            offset: int = None, size: int = None):
        """
        Returns a file object related to a given genomic resource.
        """
        resource = self.get_resource(resource_id)
        file_url = os.path.join(resource.get_url(), filename)
        return self._stream_resource_file_internal(file_url, offset, size)

    def open_file(self, resource_id: str, filename: str):
        raise NotImplementedError


class FSGenomicResourcesRepo(GenomicResourcesRepo):
    """
    A genomic score repository on a local or remote filesystem.
    """

    def __init__(self, gsd_id: str, path: str):
        super().__init__(gsd_id, path)
        self._url = pathlib.Path(self.path).absolute().as_uri()

    def _stream_resource_file_internal(self, file_uri, offset, size):
        # TODO Implement progress bar and interruptible download
        abspath = urlparse(file_uri).path
        logger.info(f"loading file: {file_uri} -> {abspath}")
        with open(abspath, "rb") as f:
            yield f.read(8192)

    def open_file(self, resource_id: str, filename: str):
        resource = self.get_resource(resource_id)
        file_url = os.path.join(resource.get_url(), filename)
        filepath = urlparse(file_url).path
        return open(filepath, "r")

    def build_repository_content(self):
        content = _create_resource_content_dict(self.root_group)
        content_filepath = os.path.join(self.path, "CONTENT.yaml")

        with open(content_filepath, "w") as out:
            yaml.dump(
                content, out, default_flow_style=False, sort_keys=False
                )

    def build_resource_manifest(self, resource_id):
        logger.info(f"generating MANIFEST files for {resource_id}")

        resource = self.get_resource(resource_id)
        assert resource is not None
        assert isinstance(resource, GenomicResource)

        cwd = urlparse(resource.get_url()).path

        command = \
            "find . -type f \\( ! -iname \"MANIFEST\" \\)  " \
            "-exec sha256sum {} \\; | sed \"s|\\s\\./||\"" \
            "> MANIFEST"

        logger.info(f"going to execute <{command}> in wd <{cwd}>")
        call(command, cwd=cwd, shell=True)


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

        super().__init__(gsd_id, url)
        print(self.path)
        self._url = url

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
