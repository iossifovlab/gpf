# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.impala_storage.schema1.impala_genotype_storage import \
    ImpalaGenotypeStorage
from dae.filesystem_storage.in_memory.filesystem_genotype_storage import \
    FilesystemGenotypeStorage


@pytest.fixture(scope="session")
def genotype_storage_registry(fixtures_gpf_instance):
    return fixtures_gpf_instance.genotype_storage_db


@pytest.fixture(scope="session")
def quads_f1_vcf_config(fixtures_gpf_instance):
    return fixtures_gpf_instance.get_genotype_data_config("quads_f1")


def test_get_genotype_storage_ids(genotype_storage_registry):
    genotype_storage_ids = genotype_storage_registry.get_genotype_storage_ids()

    assert len(genotype_storage_ids) == 7
    assert genotype_storage_ids == [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_impala_backends",
        "genotype_filesystem",
        "genotype_filesystem2",
        "test_filesystem",
        "test_impala",
    ]


def test_get_genotype_storage_impala(genotype_storage_registry):
    genotype_impala = genotype_storage_registry.get_genotype_storage(
        "genotype_impala"
    )

    assert isinstance(genotype_impala, ImpalaGenotypeStorage)
    assert genotype_impala.storage_id == "genotype_impala"


def test_get_genotype_storage_filesystem(genotype_storage_registry):
    genotype_filesystem = genotype_storage_registry.get_genotype_storage(
        "genotype_filesystem"
    )

    assert isinstance(genotype_filesystem, FilesystemGenotypeStorage)
    assert (
        genotype_filesystem.storage_id
        == "genotype_filesystem"
    )


def test_get_default_genotype_storage(genotype_storage_registry):
    genotype_storage = genotype_storage_registry.get_default_genotype_storage()

    assert isinstance(genotype_storage, FilesystemGenotypeStorage)
    assert (
        genotype_storage.storage_id == "genotype_filesystem"
    )


def test_get_genotype_storage_missing(genotype_storage_registry):
    with pytest.raises(ValueError):
        genotype_storage_registry.get_genotype_storage("genotype_missing")
