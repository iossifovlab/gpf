# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import box
import pytest

from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.inmemory_storage.inmemory_genotype_storage import (
    InmemoryGenotypeStorage,
)


@pytest.fixture(scope="session")
def genotype_storage_registry(
    fixtures_gpf_instance: GPFInstance,
) -> GenotypeStorageRegistry:
    return cast(
        GenotypeStorageRegistry,
        fixtures_gpf_instance.genotype_storages,
    )


@pytest.fixture(scope="session")
def quads_f1_vcf_config(fixtures_gpf_instance: GPFInstance) -> box.Box:
    config = fixtures_gpf_instance.get_genotype_data_config("quads_f1")
    assert config is not None
    return config


def test_get_genotype_storage_ids(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_storage_ids = \
        genotype_storage_registry.get_all_genotype_storage_ids()

    assert len(genotype_storage_ids) == 5
    assert genotype_storage_ids == [
        "internal",
        # "genotype_impala",
        # "genotype_impala_2",
        # "genotype_impala_backends",
        "genotype_filesystem",
        "genotype_filesystem2",
        "test_filesystem",
        # "test_impala",
        "test_duckdb_storage",
    ]


def test_get_genotype_storage_duckdb(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    storage = genotype_storage_registry.get_genotype_storage(
        "test_duckdb_storage",
    )

    assert storage.storage_id == "test_duckdb_storage"


def test_get_genotype_storage_filesystem(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_filesystem = genotype_storage_registry.get_genotype_storage(
        "genotype_filesystem",
    )

    assert isinstance(genotype_filesystem, InmemoryGenotypeStorage)
    assert (
        genotype_filesystem.storage_id
        == "genotype_filesystem"
    )


def test_get_default_genotype_storage(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_storage = genotype_storage_registry.get_default_genotype_storage()

    assert isinstance(genotype_storage, InmemoryGenotypeStorage)
    assert (
        genotype_storage.storage_id == "genotype_filesystem"
    )


def test_get_genotype_storage_missing(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    with pytest.raises(
            ValueError,
            match="unknown storage id: <genotype_missing>"):
        genotype_storage_registry.get_genotype_storage("genotype_missing")
