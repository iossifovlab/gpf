# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


def test_build_backend(
    filesystem_genotype_storage, quads_f1_vcf_config, gpf_instance_2013
):
    assert filesystem_genotype_storage

    backend = filesystem_genotype_storage.build_backend(
        quads_f1_vcf_config, gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models
    )

    assert len(backend.families) == 2
    assert len(backend.families["f1"].members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_query_summary_variants(
    filesystem_genotype_storage, quads_f1_vcf_config, gpf_instance_2013
):
    assert filesystem_genotype_storage

    backend = filesystem_genotype_storage.build_backend(
        quads_f1_vcf_config, gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models
    )

    assert len(list(backend.query_summary_variants())) == 3


def test_is_impala(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_impala() is False


def test_is_filestorage(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_filestorage() is True


@pytest.mark.parametrize(
    "expected_path,build_path",
    [
        ("data_dir/study_id", ["study_id"]),
        ("data_dir/study_id/data/study_id", ["study_id", "data", "study_id"]),
    ],
)
def test_get_data_dir(
    fixture_dirname, filesystem_genotype_storage, expected_path, build_path
):
    assert filesystem_genotype_storage.get_data_dir(
        *build_path
    ) == fixture_dirname(expected_path)
