from __future__ import annotations

import os
import yaml
import pathlib
import logging

from typing import Type, Optional, cast

from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .cached_repository import GenomicResourceCachedRepo
from .group_repository import GenomicResourceGroupRepo


logger = logging.getLogger(__name__)
_registered_real_genomic_resource_repository_types: dict = {}


def register_real_genomic_resource_repository_type(
        tp: str, constructor: Type[GenomicResourceRealRepo]):
    _registered_real_genomic_resource_repository_types[tp] = constructor


DEFAULT_DEFINITION = {
    "id": "default",
    "type": "url",
    # "url": "https://www.iossifovlab.com/distribution/"
    #        "public/genomic-resources-repository/"
    "url": "https://grr.seqpipe.org/"
}


def load_definition_file(filename) -> dict:
    with open(filename) as F:
        return cast(dict, yaml.safe_load(F))


GRR_DEFINITION_FILE_ENV = "GRR_DEFINITION_FILE"


def get_configured_definition():
    logger.info("using default GRR definitions")
    env_repo_definition_path = os.environ.get(GRR_DEFINITION_FILE_ENV)
    if env_repo_definition_path is not None:
        logger.debug(
            f"loading GRR definition from environment variable "
            f"{GRR_DEFINITION_FILE_ENV}="
            f"{env_repo_definition_path}")
        return load_definition_file(env_repo_definition_path)

    default_repo_definition_path = f"{os.environ['HOME']}/.grr_definition.yaml"
    logger.debug(
        f"checking default repo definition at "
        f"{default_repo_definition_path}")
    if pathlib.Path(default_repo_definition_path).exists():
        logger.debug(
            f"using repo definition at {default_repo_definition_path}")
        return load_definition_file(default_repo_definition_path)

    return DEFAULT_DEFINITION


def build_genomic_resource_repository(
        definition: Optional[dict] = None,
        file_name: str = None) -> GenomicResourceRepo:

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

    repo_type = definition["type"]

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
        repo_id = definition.get("repo_id")
        repo = GenomicResourceGroupRepo([
            build_genomic_resource_repository(child_def)
            for child_def in definition["children"]
        ], repo_id=repo_id)
    elif repo_type in _registered_real_genomic_resource_repository_types:
        repo_id = definition["id"]
        repo = _registered_real_genomic_resource_repository_types[repo_type](
            repo_id, **definition)
    else:
        raise ValueError(f"unknown genomic repository type {repo_type}")
    if "cache_dir" in definition:
        return GenomicResourceCachedRepo(repo, definition["cache_dir"])
    return repo
