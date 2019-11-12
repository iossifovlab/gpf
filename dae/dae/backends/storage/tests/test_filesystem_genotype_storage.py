import pytest

from dae.backends.storage.tests.conftest import relative_to_this_test_folder


def test_get_backend(
        filesystem_genotype_storage, quads_f1_vcf_config, genomes_db):
    assert filesystem_genotype_storage

    backend = filesystem_genotype_storage.get_backend(
        quads_f1_vcf_config.id, genomes_db
    )

    assert len(backend.families.families_list()) == 1
    assert len(backend.families.get_family('f1').members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_is_impala(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_impala() is False


def test_is_filestorage(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_filestorage() is True


@pytest.mark.parametrize('abs_path,path', [
    ('fixtures/data_dir/study_id', ['study_id']),
    ('fixtures/data_dir/study_id/data/study_id',
     ['study_id', 'data', 'study_id']),
])
def test_get_data_dir(filesystem_genotype_storage, abs_path, path):
    assert filesystem_genotype_storage.get_data_dir(*path) == \
        relative_to_this_test_folder(abs_path)
