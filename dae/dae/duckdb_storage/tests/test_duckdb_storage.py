# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genotype_storage.genotype_storage_registry import \
    get_genotype_storage_factory
from dae.import_tools.import_tools import get_import_storage_factory

from dae.duckdb_storage.duckdb_genotype_storage import \
    DuckDbGenotypeStorage
from dae.duckdb_storage.duckdb_import_storage import \
    DuckDbImportStorage


@pytest.fixture(scope="session")
def duckdb_storage_config(tmp_path_factory):
    storage_path = tmp_path_factory.mktemp("duckdb_storage")
    return {
        "id": "dev_duckdb_storage",
        "storage_type": "duckdb",
        "db": f"{storage_path}/dev_storage.duckdb",
    }


@pytest.fixture(scope="session")
def gcp_storage_fixture(duckdb_storage_config):
    storage_factory = get_genotype_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory(duckdb_storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbGenotypeStorage)
    return storage.start()


def test_genotype_storage_config(duckdb_storage_config):
    storage_factory = get_genotype_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory(duckdb_storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbGenotypeStorage)


def test_import_storage_config(duckdb_storage_config):
    storage_factory = get_import_storage_factory("duckdb")
    assert storage_factory is not None
    storage = storage_factory()
    assert storage is not None
    assert isinstance(storage, DuckDbImportStorage)
