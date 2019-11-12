import pytest

from dae.backends.storage.tests.conftest import relative_to_this_test_folder


def test_get_backend(impala_genotype_storage, quads_f1_config, genomes_db):
    assert impala_genotype_storage

    backend = impala_genotype_storage.get_backend(
        quads_f1_config.id, genomes_db
    )

    assert len(backend.families.families_list()) == 1
    assert len(backend.families.get_family('f1').members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_is_impala(impala_genotype_storage):
    assert impala_genotype_storage.is_impala() is True


def test_is_filestorage(impala_genotype_storage):
    assert impala_genotype_storage.is_filestorage() is False


@pytest.mark.parametrize('hdfs_dir,path', [
    ('/tmp/test_data/study_id', ['study_id']),
    ('/tmp/test_data/study_id/pedigree', ['study_id', 'pedigree']),
])
def test_get_hdfs_dir(impala_genotype_storage, hdfs_dir, path):
    if impala_genotype_storage.hdfs_helpers.exists(hdfs_dir):
        impala_genotype_storage.hdfs_helpers.delete(hdfs_dir, recursive=True)

    assert impala_genotype_storage.hdfs_helpers.exists(hdfs_dir) is False

    assert impala_genotype_storage.get_hdfs_dir(*path) == hdfs_dir

    assert impala_genotype_storage.hdfs_helpers.exists(hdfs_dir) is True


def test_impala_connection(impala_genotype_storage):
    impala_connection = impala_genotype_storage.impala_connection

    assert impala_connection is not None


def test_impala_helpers(impala_genotype_storage):
    impala_helpers = impala_genotype_storage.impala_helpers

    assert impala_helpers is not None
    assert impala_helpers.connection is not None


def test_hdfs_helpers(impala_genotype_storage, hdfs_host):
    hdfs_helpers = impala_genotype_storage.hdfs_helpers

    assert hdfs_helpers is not None

    assert hdfs_helpers.host == hdfs_host
    assert hdfs_helpers.port == 8020
    assert hdfs_helpers.hdfs is not None


def test_impala_load_study(impala_genotype_storage, genomes_db):
    impala_genotype_storage.impala_helpers.drop_database(
        'impala_storage_test_db'
    )

    impala_genotype_storage.impala_load_study(
        'study_id',
        relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/pedigree'),
        relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/variants')
    )

    backend = impala_genotype_storage.get_backend(
        'study_id', genomes_db
    )

    assert len(backend.families.families_list()) == 1
    assert len(backend.families.get_family('f1').members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_impala_config(impala_genotype_storage):
    impala_config = impala_genotype_storage._impala_config(
        'study_id',
        relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/pedigree'),
        relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/variants')
    )

    assert list(impala_config.keys()) == ['db', 'tables', 'files']


def test_impala_storage_config(impala_genotype_storage):
    impala_storage_config = \
        impala_genotype_storage._impala_storage_config('study_id')

    assert impala_storage_config.db == 'impala_storage_test_db'
    assert impala_storage_config.tables.pedigree == 'study_id_pedigree'
    assert impala_storage_config.tables.variant == 'study_id_variant'


def test_hdfs_parquet_files_config(impala_genotype_storage):
    if impala_genotype_storage.hdfs_helpers.exists('/tmp/test_data/study_id'):
        impala_genotype_storage.hdfs_helpers.delete(
            '/tmp/test_data/study_id', recursive=True
        )

    hdfs_parquet_files_config = \
        impala_genotype_storage._hdfs_parquet_files_config(
            'study_id',
            relative_to_this_test_folder(
                'fixtures/studies/quads_f1_impala/data/pedigree'),
            relative_to_this_test_folder(
                'fixtures/studies/quads_f1_impala/data/variants')
        )

    assert hdfs_parquet_files_config.files.pedigree == \
        ['/tmp/test_data/study_id/pedigree/quads_f1_impala_pedigree.parquet']
    assert hdfs_parquet_files_config.files.variants == [
        '/tmp/test_data/study_id/variants/quads_f1_impala_variant_000001.'
        'parquet'
    ]
