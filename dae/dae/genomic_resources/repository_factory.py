from __future__ import annotations

import os
import yaml
import pathlib
import logging

from typing import Type

from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .cached_repository import GenomicResourceCachedRepo
from .group_repository import GenomicResourceGroupRepo


logger = logging.getLogger(__name__)
_registered_real_genomic_resource_repository_types = {}


def register_real_genomic_resource_repository_type(
        tp: str, constructor: Type[GenomicResourceRealRepo]):
    _registered_real_genomic_resource_repository_types[tp] = constructor


DEFAULT_DEFINITION = {
    "id": "default",
    "type": "url",
    "url": "https://www.iossifovlab.com/distribution/"
           "public/genomic-resources-repository/"
}


def load_definition_file(filename):
    with open(filename) as F:
        return yaml.safe_load(F)


GRR_DEFINITION_FILE_ENV = "GRR_DEFINITION_FILE"


def get_configured_definition():
    if GRR_DEFINITION_FILE_ENV is os.environ:
        return load_definition_file(os.environ[GRR_DEFINITION_FILE_ENV])

    default_repo_definition_path = f"{os.environ['HOME']}/.grr_definition.yaml"
    logger.debug(f"checking repo definition at {default_repo_definition_path}")
    if pathlib.Path(default_repo_definition_path).exists():
        logger.debug(
            f"using repo definition at {default_repo_definition_path}")
        return load_definition_file(default_repo_definition_path)

    return DEFAULT_DEFINITION


def build_genomic_resource_repository(
        definition: dict = None, file_name: str = None) -> GenomicResourceRepo:

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

    if "type" not in definition:
        raise ValueError(
            f"The repository definition element {definition} "
            "has not type attiribute.")

    repo_type = definition["type"]

    if repo_type == "group":
        if "children" not in definition:
            raise ValueError(
                f"The definition for group repository {definition} "
                "has no children attiribute.")
        if not isinstance(definition["children"], list):
            raise ValueError(
                "The children attribute in the definition of a group "
                "repository must be a list")
        repo = GenomicResourceGroupRepo([
            build_genomic_resource_repository(child_def)
            for child_def in definition["children"]
        ])
    elif repo_type in _registered_real_genomic_resource_repository_types:
        repo_id = definition["id"]
        repo = _registered_real_genomic_resource_repository_types[repo_type](
            repo_id, **definition)
    else:
        raise ValueError(f"unknown genomic repository type {repo_type}")
    if "cache_dir" in definition:
        return GenomicResourceCachedRepo(repo, definition["cache_dir"])
    return repo
