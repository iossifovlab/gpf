# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.duckdb_storage.duckdb_genotype_storage import DuckDbParquetStorage
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="session")
def genotype_storage_registry(
    t4c8_instance: GPFInstance,
) -> GenotypeStorageRegistry:
    return cast(
        GenotypeStorageRegistry,
        t4c8_instance.genotype_storages,
    )


def test_get_genotype_storage_ids(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_storage_ids = \
        genotype_storage_registry.get_all_genotype_storage_ids()

    assert len(genotype_storage_ids) == 2
    assert genotype_storage_ids == [
        "internal",
        "duckdb_wgpf_test",
    ]


def test_get_genotype_storage_duckdb(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    storage = genotype_storage_registry.get_genotype_storage(
        "duckdb_wgpf_test",
    )

    assert storage.storage_id == "duckdb_wgpf_test"


def test_get_genotype_storage_filesystem(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_filesystem = genotype_storage_registry.get_genotype_storage(
        "internal",
    )

    assert isinstance(genotype_filesystem, DuckDbParquetStorage)
    assert (
        genotype_filesystem.storage_id
        == "internal"
    )


def test_get_default_genotype_storage(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    genotype_storage = genotype_storage_registry.get_default_genotype_storage()

    assert isinstance(genotype_storage, DuckDbParquetStorage)
    assert (
        genotype_storage.storage_id == "duckdb_wgpf_test"
    )


def test_get_genotype_storage_missing(
    genotype_storage_registry: GenotypeStorageRegistry,
) -> None:
    with pytest.raises(
            ValueError,
            match="unknown storage id: <genotype_missing>"):
        genotype_storage_registry.get_genotype_storage("genotype_missing")
