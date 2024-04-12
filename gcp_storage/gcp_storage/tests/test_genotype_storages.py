# pylint: disable=W0621,C0114,C0116,W0212,W0613
# import pytest

# from dae.utils.regions import Region

from dae.genotype_storage.genotype_storage_registry import \
    get_genotype_storage_factory
from dae.import_tools.import_tools import get_import_storage_factory

from gcp_storage.gcp_genotype_storage import GcpGenotypeStorage
from gcp_storage.gcp_import_storage import GcpImportStorage


def test_genotype_storage_config(gcp_storage_config):
    storage_factory = get_genotype_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory(gcp_storage_config)
    assert storage is not None
    assert isinstance(storage, GcpGenotypeStorage)


def test_import_storage_config(gcp_storage_config):
    storage_factory = get_import_storage_factory("gcp")
    assert storage_factory is not None
    storage = storage_factory()
    assert storage is not None
    assert isinstance(storage, GcpImportStorage)


def test_imported_study(imported_study):
    assert imported_study is not None
