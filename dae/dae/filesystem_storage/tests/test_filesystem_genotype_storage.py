# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

# from dae.filesystem_storage.filesystem_genotype_storage import \
#     FilesystemGenotypeStorage
from dae.import_tools.import_tools import run_with_project


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
    assert filesystem_genotype_storage.get_storage_type() == "filesystem"


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
