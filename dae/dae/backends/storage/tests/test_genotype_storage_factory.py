from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.backends.storage.filesystem_genotype_storage import (
    FilesystemGenotypeStorage,
)


def test_get_genotype_storage_ids(genotype_storage_factory):
    genotype_storage_ids = genotype_storage_factory.get_genotype_storage_ids()

    assert len(genotype_storage_ids) == 6
    assert genotype_storage_ids == [
        "genotype_impala",
        "genotype_impala_backends",
        "genotype_filesystem",
        "genotype_filesystem2",
        "test_filesystem",
        "test_impala",
    ]


def test_get_genotype_storage_impala(genotype_storage_factory):
    genotype_impala = genotype_storage_factory.get_genotype_storage(
        "genotype_impala"
    )

    assert isinstance(genotype_impala, ImpalaGenotypeStorage)
    assert genotype_impala.storage_id == "genotype_impala"


def test_get_genotype_storage_filesystem(genotype_storage_factory):
    genotype_filesystem = genotype_storage_factory.get_genotype_storage(
        "genotype_filesystem"
    )

    assert isinstance(genotype_filesystem, FilesystemGenotypeStorage)
    assert (
        genotype_filesystem.storage_id
        == "genotype_filesystem"
    )


def test_get_default_genotype_storage(genotype_storage_factory):
    genotype_storage = genotype_storage_factory.get_default_genotype_storage()

    assert isinstance(genotype_storage, FilesystemGenotypeStorage)
    assert (
        genotype_storage.storage_id == "genotype_filesystem"
    )


def test_get_genotype_storage_missing(genotype_storage_factory):
    genotype_missing = genotype_storage_factory.get_genotype_storage(
        "genotype_missing"
    )

    assert genotype_missing is None
