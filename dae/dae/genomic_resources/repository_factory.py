"""Provides a factory for building genomic resources repostiories."""

from __future__ import annotations

import os
import pathlib
import logging
import tempfile

from typing import Optional, List, cast
from urllib.parse import urlparse

import yaml

from .fsspec_protocol import build_fsspec_protocol
from .repository import GenomicResourceRepo, GenomicResourceProtocolRepo
from .cached_repository import GenomicResourceCachedRepo
from .testing import build_testing_protocol

from .group_repository import GenomicResourceGroupRepo


logger = logging.getLogger(__name__)

# _registered_genomic_resource_repository_protocol_types: \
#     dict[str, Type[
#         Union[ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol]]] = {}


# def register_genomic_resource_repository_protocol_type(
#         protocol_type: str,
#         constructor: Type[
#             Union[ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol]]):
#     _registered_genomic_resource_repository_protocol_types[
#         protocol_type] = constructor


DEFAULT_DEFINITION = {
    "id": "default",
    "type": "http",
    "url": "https://www.iossifovlab.com/distribution/"
           "public/genomic-resources-repository/",
    # "url": "https://grr.seqpipe.org/",
}


def load_definition_file(filename):
    """Load GRR definition from a YAML file."""
    with open(filename, "rt", encoding="utf8") as infile:
        return yaml.safe_load(infile)


GRR_DEFINITION_FILE_ENV = "GRR_DEFINITION_FILE"


def get_configured_definition():
    """Return default genomic resources repository definition."""
    logger.info("using default GRR definitions")
    env_repo_definition_path = os.environ.get(GRR_DEFINITION_FILE_ENV)
    if env_repo_definition_path is not None:
        logger.debug(
            "loading GRR definition from environment variable %s=%s",
            GRR_DEFINITION_FILE_ENV, env_repo_definition_path)
        return load_definition_file(env_repo_definition_path)

    default_repo_definition_path = f"{os.environ['HOME']}/.grr_definition.yaml"
    logger.debug(
        "checking default repo definition at %s",
        default_repo_definition_path)
    if pathlib.Path(default_repo_definition_path).exists():
        logger.debug(
            "using repo definition at %s", default_repo_definition_path)
        return load_definition_file(default_repo_definition_path)

    return DEFAULT_DEFINITION


def _build_real_repository(
        proto_type: str = "",
        repo_id: str = "",
        **kwargs) -> GenomicResourceRepo:
    # pylint: disable=too-many-branches
    if proto_type == "group":
        repo = _build_group_repository(
            repo_id=repo_id, **kwargs)

    elif proto_type in {"file", "dir", "directory"}:
        root_url = kwargs.pop("directory")

        if root_url is None:
            raise ValueError("missing root url for a file/dir repository")

        if not os.path.isabs(root_url):
            logger.error(
                "for directory/file resources repository we expects an "
                "absolute directory name: %s", root_url)
            raise ValueError(f"not an absolute directory name: {root_url}")
        root_url = f"file://{root_url}"
        protocol = build_fsspec_protocol(repo_id, root_url, **kwargs)
        repo = GenomicResourceProtocolRepo(protocol)

    elif proto_type == "url":
        root_url = kwargs.pop("url")
        parsed = urlparse(root_url)
        if parsed.scheme not in {"http", "https", "s3"}:
            raise ValueError(f"unexpected GRR protocol scheme {root_url}")
        protocol = build_fsspec_protocol(repo_id, root_url, **kwargs)
        repo = GenomicResourceProtocolRepo(protocol)

    elif proto_type == "http":
        root_url = kwargs.pop("url")

        if urlparse(root_url).scheme not in {"http", "https"}:
            raise ValueError(f"not an http(s) root url: {root_url}")
        protocol = build_fsspec_protocol(repo_id, root_url)
        repo = GenomicResourceProtocolRepo(protocol)

    elif proto_type == "s3":
        root_url = kwargs.pop("url")

        if urlparse(root_url).scheme != "s3":
            raise ValueError(f"not an s3 root url: {root_url}")
        protocol = build_fsspec_protocol(repo_id, root_url, **kwargs)
        repo = GenomicResourceProtocolRepo(protocol)

    elif proto_type in {"embedded", "memory"}:
        root_url = tempfile.mkdtemp(prefix="memory", suffix=repo_id)
        if not os.path.isabs(root_url):
            logger.error(
                "for embedded resources repository we expects an "
                "absolute url: %s", root_url)
            raise ValueError(f"not an absolute root url: {root_url}")

        content = kwargs.get("content", {})
        protocol = build_testing_protocol(
            content=content,
            scheme="memory",
            proto_id=repo_id,
            root_path=root_url)
        repo = GenomicResourceProtocolRepo(protocol)

    else:
        raise ValueError(f"unexpected GRR protocol type {proto_type}")

    if "cache_dir" not in kwargs:
        return repo

    cache_dir = kwargs.pop("cache_dir")
    return GenomicResourceCachedRepo(repo, f"file://{cache_dir}")


def _build_group_repository(
        repo_id: str,
        children: List[dict], **kwargs) -> GenomicResourceRepo:

    result: List[GenomicResourceRepo] = []
    for child in children:
        child_id: str = child.pop("id", "")
        proto_type = child.pop("type")
        if proto_type == "group":
            repo: GenomicResourceRepo = \
                _build_group_repository(
                    child_id, child.pop("children"), **child)
            result.append(repo)
            continue

        repo = _build_real_repository(
            proto_type=proto_type, repo_id=child_id, **child)
        result.append(repo)

    repo = GenomicResourceGroupRepo(result, repo_id)

    if "cache_dir" not in kwargs:
        return repo

    cache_dir = kwargs.pop("cache_dir")
    return GenomicResourceCachedRepo(repo, f"file://{cache_dir}")


def build_genomic_resource_repository(
        definition: Optional[dict] = None,
        file_name: str = None) -> GenomicResourceRepo:
    """Build a GRR using a definition dict or yaml file."""
    if not definition:
        if file_name is not None:
            definition = load_definition_file(file_name)
        else:
            definition = get_configured_definition()
    else:
        if file_name is not None:
            raise ValueError(
                "only one of the definition and file_name parameters"
                "should be provided")

    if definition is None:
        raise ValueError("can't find GRR definition")

    if "type" not in definition:
        raise ValueError(
            f"The repository definition element {definition} "
            "has not type attiribute.")

    repo_type = definition.pop("type")
    repo_id = definition.pop("id", None)

    if repo_type == "group":
        if "children" not in definition:
            raise ValueError(
                f"The definition for group repository {definition} "
                "has no children attiribute.")
        if not isinstance(definition["children"], list) and \
                not isinstance(definition["children"], tuple):
            raise ValueError(
                "The children attribute in the definition of a group "
                "repository must be a list")
        repo_id = definition.get("id")

        children = cast(List[dict], definition.pop("children"))
        repo: GenomicResourceRepo = \
            _build_group_repository(repo_id, children, **definition)
    else:
        repo = _build_real_repository(repo_type, repo_id, **definition)

    return repo
