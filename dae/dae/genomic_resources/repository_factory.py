"""Provides a factory for building genomic resources repostiories."""

from __future__ import annotations

import os
import copy
import pathlib
import logging
import tempfile

from typing import Optional, cast, Any
from urllib.parse import urlparse

import yaml

from .fsspec_protocol import build_fsspec_protocol, build_inmemory_protocol
from .repository import GenomicResourceRepo, GenomicResourceProtocolRepo, \
    GenomicResource
from .cached_repository import GenomicResourceCachedRepo
from .resource_implementation import GenomicResourceImplementation

from .group_repository import GenomicResourceGroupRepo

logger = logging.getLogger(__name__)


DEFAULT_DEFINITION = {
    "id": "default",
    "type": "http",
    "url": "https://storage.googleapis.com/iossifovlab-grr",

    # "url": "https://www.iossifovlab.com/distribution/"
    #        "public/genomic-resources-repository/",
    # "url": "https://grr.seqpipe.org/",
}


def load_definition_file(filename: str) -> Any:
    """Load GRR definition from a YAML file."""
    with open(filename, "rt", encoding="utf8") as infile:
        return yaml.safe_load(infile)


GRR_DEFINITION_FILE_ENV = "GRR_DEFINITION_FILE"


def get_default_grr_definition_path() -> Optional[str]:
    """Return a path to default genomic resources repository definition."""
    env_repo_definition_path = os.environ.get(GRR_DEFINITION_FILE_ENV)
    if env_repo_definition_path is not None:
        logger.debug(
            "found GRR definition from environment variable %s=%s",
            GRR_DEFINITION_FILE_ENV, env_repo_definition_path)
        return env_repo_definition_path
    default_repo_definition_path = f"{os.environ['HOME']}/.grr_definition.yaml"
    logger.debug(
        "checking default GRR definition at %s",
        default_repo_definition_path)
    if pathlib.Path(default_repo_definition_path).exists():
        logger.debug(
            "found GRR definition at %s", default_repo_definition_path)
        return default_repo_definition_path
    return None


def get_default_grr_definition() -> dict[str, Any]:
    """Return default genomic resources repository definition."""
    logger.info("using default GRR definitions")
    definition_path = get_default_grr_definition_path()
    if definition_path:
        return cast(dict[str, Any], load_definition_file(definition_path))
    return copy.deepcopy(DEFAULT_DEFINITION)


def _build_real_repository(
        proto_type: str = "",
        repo_id: str = "",
        **kwargs: Any) -> GenomicResourceRepo:
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
        content = kwargs.get("content", {})
        protocol = build_inmemory_protocol(repo_id, root_url, content)
        repo = GenomicResourceProtocolRepo(protocol)

    else:
        raise ValueError(f"unexpected GRR protocol type {proto_type}")

    if "cache_dir" not in kwargs:
        return repo

    cache_dir = kwargs.pop("cache_dir")
    return GenomicResourceCachedRepo(repo, f"file://{cache_dir}")


def _build_group_repository(
        repo_id: str,
        children: list[dict], **kwargs: Any) -> GenomicResourceRepo:

    result: list[GenomicResourceRepo] = []
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


def build_genomic_resource_group_repository(
        repo_id: str,
        children: list[GenomicResourceRepo]) -> GenomicResourceRepo:
    return GenomicResourceGroupRepo(children, repo_id)


def build_genomic_resource_repository(
        definition: Optional[dict] = None,
        file_name: Optional[str] = None) -> GenomicResourceRepo:
    """Build a GRR using a definition dict or yaml file."""
    if not definition:
        if file_name is not None:
            definition = load_definition_file(file_name)
        else:
            definition = get_default_grr_definition()
    else:
        if file_name is not None:
            raise ValueError(
                "only one of the definition and file_name parameters"
                "should be provided")

    if definition is None:
        raise ValueError("can't find GRR definition")

    if "type" not in definition:
        logger.error(
            "missing type in genomic resources repository definition: %s",
            definition)
        raise ValueError(
            f"The repository definition element {definition} "
            "has no type attiribute.")

    orig_definition = copy.deepcopy(definition)

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

        children = cast(list[dict], definition.pop("children"))
        repo: GenomicResourceRepo = \
            _build_group_repository(repo_id, children, **definition)
    else:
        repo = _build_real_repository(repo_type, repo_id, **definition)
    repo.definition = orig_definition

    return repo


def build_resource_implementation(
        res: GenomicResource) -> GenomicResourceImplementation:
    """Build a resource implementation from a resource."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources import get_resource_implementation_builder

    builder = get_resource_implementation_builder(res.get_type())
    if builder is None:
        raise ValueError(
            f"unsupported resource implementation type <{res.get_type()}> "
            f"for resource <{res.resource_id}>"
        )

    return builder(res)
