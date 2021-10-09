from __future__ import annotations

import os
from typing import Type
import yaml
import pathlib


from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .cached_repository import GenomicResourceCachedRepo
from .group_repository import GenomicResourceGroupRepo


_registered_real_genomic_resource_repository_types = {}


def register_real_genomic_resource_repository_type(
        tp: str, constructor: Type[GenomicResourceRealRepo]):
    _registered_real_genomic_resource_repository_types[tp] = constructor


DEFAULT_DEFINITION = {
    "id": "defaut",
    "type": "url",
    "url": "https://iossifovlab.com/defaultGenomicResourceRepository",
    "cacheDir": "/tmp/genomicResourcesCache"
}


def parse_definition_file(filename):
    return yaml.safe_load(filename)


GRR_DEFINITION_FILE_ENV = "GRR_DEFINITION_FILE"


def get_configured_definition():
    if GRR_DEFINITION_FILE_ENV is os.environ:
        return parse_definition_file(os.environ[GRR_DEFINITION_FILE_ENV])

    if pathlib.Path("~/.grr_efinition.yaml"):
        return parse_definition_file(os.environ[GRR_DEFINITION_FILE_ENV])

    return DEFAULT_DEFINITION


def build_genomic_resource_repository(definition=None) -> GenomicResourceRepo:
    if not definition:
        definition = get_configured_definition()

    if "type" not in definition:
        raise ValueError(
            f"The repository definition element {definition} "
            "has not type attiribute.")

    repoType = definition["type"]

    if repoType == "group":
        if "children" not in definition:
            raise ValueError(
                f"The definition for group repository {definition} "
                "has no children attiribute.")
        if not isinstance(definition["children"], list):
            raise ValueError(
                "The children attribute in the definition of a group "
                "repository must be a list")
        repo = GenomicResourceGroupRepo(
            [build_genomic_resource_repository(chDef)
             for chDef in definition["children"]])
    elif repoType in _registered_real_genomic_resource_repository_types:
        repo_id = definition["id"]
        repo = _registered_real_genomic_resource_repository_types[repoType](
            repo_id, **definition)
    else:
        raise ValueError(f"unknown genomic repository type {repoType}")
    if "cacheDir" in definition:
        return GenomicResourceCachedRepo(repo, definition["cacheDir"])
    return repo
