# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genotype_storage.genotype_storage_registry import \
    get_genotype_storage_factory
from dae.import_tools.import_tools import get_import_storage_factory


from dae.duckdb_storage.duckdb_genotype_storage import \
    DuckDbGenotypeStorage
from dae.duckdb_storage.duckdb_import_storage import \
    DuckDbImportStorage


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


def test_imported_study(imported_study):
    assert imported_study is not None


def test_imported_study_family_variants(imported_study):
    vs = list(imported_study.query_variants())

    assert len(vs) == 2


def test_imported_study_summary_variants(imported_study):
    vs = list(imported_study.query_summary_variants())

    assert len(vs) == 2
