# pylint: disable=W0621,C0114,C0116,W0212,W0613
import re

import pytest

from dae.import_tools.cli import run_with_project
from dae.inmemory_storage.inmemory_genotype_storage import \
    InmemoryGenotypeStorage


@pytest.fixture(scope="module")
def filesystem_genotype_storage(simple_project):
    return simple_project.get_genotype_storage()


@pytest.fixture(scope="module")
def study_config(simple_project):
    run_with_project(simple_project)
    gpf_instance = simple_project.get_gpf_instance()
    gpf_instance.reload()

    return gpf_instance.get_genotype_data_config("test_import")


def test_build_backend(
        filesystem_genotype_storage, simple_project, study_config):
    gpf_instance = simple_project.get_gpf_instance()

    backend = filesystem_genotype_storage.build_backend(
        study_config, gpf_instance.reference_genome,
        gpf_instance.gene_models
    )

    assert len(backend.families) == 1
    assert len(backend.families["f1"].members_ids) == 5
    assert len(list(backend.query_variants())) == 2


def test_query_summary_variants(
        filesystem_genotype_storage, simple_project, study_config):

    gpf_instance = simple_project.get_gpf_instance()
    backend = filesystem_genotype_storage.build_backend(
        study_config, gpf_instance.reference_genome,
        gpf_instance.gene_models
    )

    assert len(list(backend.query_summary_variants())) == 2


def test_storage_type(filesystem_genotype_storage):
    assert filesystem_genotype_storage.get_storage_type() == "inmemory"


@pytest.mark.parametrize(
    "expected_path,build_path",
    [
        ("storage/study_id", ["study_id"]),
        ("storage/study_id/data/study_id", ["study_id", "data", "study_id"]),
    ],
)
def test_get_data_dir(
    fixture_dirname, filesystem_genotype_storage, expected_path, build_path
):
    assert filesystem_genotype_storage.get_data_dir(
        *build_path).endswith(expected_path)


def test_create_filesystem_storage(tmp_path):
    config = {
        "storage_type": "inmemory",
        "id": "aaaa",
        "dir": str(tmp_path)
    }
    storage = InmemoryGenotypeStorage(config)
    assert storage is not None


def test_create_filesystem_storage_missing_id(tmp_path):
    config = {
        "storage_type": "inmemory",
        # "id": "aaaa",
        "dir": str(tmp_path)
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without ID; 'id' is required"):
        InmemoryGenotypeStorage(config)


def test_create_missing_storage_type():
    config = {
        "id": "aaaa",
        "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without type; 'storage_type' is required"):
        InmemoryGenotypeStorage(config)


def test_create_wrong_storage_type():
    config = {
        "id": "aaaa",
        "storage_type": "filesystem2",
        "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "storage configuration for <filesystem2> passed to "
                "genotype storage class type <inmemory>")):
        InmemoryGenotypeStorage(config)


def test_create_missing_dir():
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


def test_create_bad_dir():
    config = {
        "id": "aaaa",
        "storage_type": "inmemory",
        "dir": "tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for inmemory storage: "
                "{'dir': ['path <tmp/aaaa_filesystem> "
                "is not an absolute path']}")):
        InmemoryGenotypeStorage(config)
