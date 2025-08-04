# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import re
from typing import cast

import pytest
from box import Box
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.inmemory_storage.inmemory_genotype_storage import (
    InmemoryGenotypeStorage,
)


@pytest.fixture(scope="module")
def filesystem_genotype_storage(
    simple_project: ImportProject,
) -> GenotypeStorage:
    return simple_project.get_genotype_storage()


@pytest.fixture(scope="module")
def study_config(simple_project: ImportProject) -> Box:
    run_with_project(simple_project)
    gpf_instance = simple_project.get_gpf_instance()
    gpf_instance.reload()

    config = gpf_instance.get_genotype_data_config("test_import")
    assert config is not None
    return config


def test_build_backend(
    filesystem_genotype_storage: GenotypeStorage,
    simple_project: ImportProject,
    study_config: Box,
) -> None:
    gpf_instance = simple_project.get_gpf_instance()

    filesystem_genotype_storage.build_backend(
        study_config, gpf_instance.reference_genome,
        gpf_instance.gene_models,
    )

    backend = filesystem_genotype_storage.loaded_variants[study_config["id"]]
    registry = gpf_instance.genotype_storages

    assert len(backend.families) == 1
    assert len(backend.families["f1"].members_ids) == 5
    assert len(list(
        registry.query_variants([study_config["id"]], {}),
    )) == 2


def test_query_summary_variants(
    filesystem_genotype_storage: GenotypeStorage,
    simple_project: ImportProject,
    study_config: Box,
) -> None:

    gpf_instance = simple_project.get_gpf_instance()
    filesystem_genotype_storage.build_backend(
        study_config, gpf_instance.reference_genome,
        gpf_instance.gene_models,
    )
    registry = gpf_instance.genotype_storages

    assert len(list(
        registry.query_summary_variants([study_config["id"]], {}),
    )) == 2


def test_storage_type(
    filesystem_genotype_storage: GenotypeStorage,
) -> None:
    assert filesystem_genotype_storage.storage_type == "inmemory"


@pytest.mark.parametrize(
    "expected_path,build_path",
    [
        ("storage/study_id", ["study_id"]),
        ("storage/study_id/data/study_id", ["study_id", "data", "study_id"]),
    ],
)
def test_get_data_dir(
    filesystem_genotype_storage: GenotypeStorage,
    expected_path: str,
    build_path: str,
) -> None:
    storage = cast(InmemoryGenotypeStorage, filesystem_genotype_storage)
    assert storage.get_data_dir(*build_path).endswith(expected_path)


def test_create_filesystem_storage(tmp_path: pathlib.Path) -> None:
    config = {
        "storage_type": "inmemory",
        "id": "aaaa",
        "dir": str(tmp_path),
    }
    storage = InmemoryGenotypeStorage(config)
    assert storage is not None


def test_create_filesystem_storage_missing_id(tmp_path: pathlib.Path) -> None:
    config = {
        "storage_type": "inmemory",
        "dir": str(tmp_path),
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without ID; 'id' is required"):
        InmemoryGenotypeStorage(config)


def test_create_missing_storage_type() -> None:
    config = {
        "id": "aaaa",
        "dir": "/ttt/aaaa_filesystem",
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without type; 'storage_type' is required"):
        InmemoryGenotypeStorage(config)


def test_create_wrong_storage_type() -> None:
    config = {
        "id": "aaaa",
        "storage_type": "filesystem2",
        "dir": "/ttt/aaaa_filesystem",
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "storage configuration for <filesystem2> passed to "
                "genotype storage class type <{'inmemory'}>")):
        InmemoryGenotypeStorage(config)


def test_create_missing_dir() -> None:
    config = {
        "id": "aaaa",
        "storage_type": "inmemory",
        # "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for inmemory storage: "
                "{'dir': ['required field']}")):
        InmemoryGenotypeStorage(config)


def test_create_bad_dir() -> None:
    config = {
        "id": "aaaa",
        "storage_type": "inmemory",
        "dir": "tmp/aaaa_filesystem",
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for inmemory storage: "
                "{'dir': ['path <tmp/aaaa_filesystem> "
                "is not an absolute path']}")):
        InmemoryGenotypeStorage(config)
