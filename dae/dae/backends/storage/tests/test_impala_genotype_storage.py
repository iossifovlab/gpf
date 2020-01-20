import pytest
import os

from box import Box

from dae.backends.storage.tests.conftest import relative_to_this_test_folder


def test_build_backend(
        impala_genotype_storage, quads_f1_config, genomes_db_2013):
    assert impala_genotype_storage

    backend = impala_genotype_storage.build_backend(
        quads_f1_config, genomes_db_2013.get_genome()
    )

    assert len(backend.families) == 1
    assert len(backend.families['f1'].members_ids) == 5
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


def test_impala_load_study(impala_genotype_storage, genomes_db_2013):
    impala_genotype_storage.impala_helpers.drop_database(
        'impala_storage_test_db'
    )

    impala_genotype_storage.impala_load_study(
        'study_id',
        [relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/variants')],
        [relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/pedigree')]
    )

    backend = impala_genotype_storage.build_backend(
        Box({'id': 'study_id'}, default_box=True),
        genomes_db_2013.get_genome()
    )

    assert len(backend.families) == 1
    assert len(backend.families['f1'].members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_impala_partition_import(
        impala_genotype_storage, genomes_db_2013,
        fixture_dirname):

    ped_file = fixture_dirname('backends/test_partition/pedigree.parquet')
    variants_path = fixture_dirname('backends/test_partition/variants.parquet')

    impala_genotype_storage.impala_load_dataset(
        'test_study',
        variants_path,
        ped_file)

    hdfs = impala_genotype_storage.hdfs_helpers
    root = impala_genotype_storage.storage_config.hdfs.base_dir

    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=1_8/family_bin=6/coding_bin=0/'
        'frequency_bin=3'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=1_8/family_bin=6/coding_bin=0/'
        'frequency_bin=3/'
        'variants_region_bin_1_8_family_bin_6_'
        'coding_bin_0_frequency_bin_3.parquet'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=1_8/family_bin=69'
        '/coding_bin=0/frequency_bin=3'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=1_8/family_bin=69/coding_bin=0/'
        'frequency_bin=3/'
        'variants_region_bin_1_8_family_bin_69_'
        'coding_bin_0_frequency_bin_3.parquet'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=2_9/family_bin=6/coding_bin=0/'
        'frequency_bin=3'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=2_9/family_bin=6/coding_bin=0/'
        'frequency_bin=3/'
        'variants_region_bin_2_9_family_bin_6_'
        'coding_bin_0_frequency_bin_3.parquet'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=2_9/family_bin=69'
        '/coding_bin=0/frequency_bin=3'))
    assert hdfs.exists(os.path.join(
        root,
        'test_study/variants/region_bin=2_9/family_bin=69/coding_bin=0/'
        'frequency_bin=3/'
        'variants_region_bin_2_9_family_bin_69_'
        'coding_bin_0_frequency_bin_3.parquet'))

    impala = impala_genotype_storage.impala_helpers
    db = impala_genotype_storage.storage_config.impala.db

    with impala.connection.cursor() as cursor:
        cursor.execute(f'DESCRIBE EXTENDED {db}.test_study_variants')
        rows = list(cursor)
        assert any(
                row[1] == 'gpf_partitioning_coding_bin_coding_effect_types'
                and row[2] == 'missense, nonsense, frame-shift, synonymous'
                for row in rows)
        assert any(
                row[1] == 'gpf_partitioning_family_bin_family_bin_size'
                and int(row[2]) == 100
                for row in rows)
        assert any(
                row[1] == 'gpf_partitioning_frequency_bin_rare_boundary'
                and int(row[2]) == 30
                for row in rows)
        assert any(
                row[1] == 'gpf_partitioning_region_bin_chromosomes'
                and '1, 2' in row[2]
                for row in rows)
        assert any(
                row[1] == 'gpf_partitioning_region_bin_region_length'
                and int(row[2]) == 100000
                for row in rows)

# def test_impala_config(impala_genotype_storage):
#     impala_config = impala_genotype_storage._impala_config(
#         'study_id',
#         relative_to_this_test_folder(
#             'fixtures/studies/quads_f1_impala/data/pedigree'),
#         relative_to_this_test_folder(
#             'fixtures/studies/quads_f1_impala/data/variants')
#     )

#     assert list(impala_config.keys()) == ['db', 'tables', 'files']


# def test_impala_storage_config(impala_genotype_storage):
#     impala_storage_config = \
#         impala_genotype_storage._impala_storage_config('study_id')

#     assert impala_storage_config.db == 'impala_storage_test_db'
#     assert impala_storage_config.tables.pedigree == 'study_id_pedigree'
#     assert impala_storage_config.tables.variant == 'study_id_variant'


# def test_hdfs_parquet_files_config(impala_genotype_storage):
#     if impala_genotype_storage.hdfs_helpers.exists(
#             '/tmp/test_data/study_id'):
#         impala_genotype_storage.hdfs_helpers.delete(
#             '/tmp/test_data/study_id', recursive=True
#         )

#     hdfs_parquet_files_config = \
#         impala_genotype_storage._hdfs_parquet_files_config(
#             'study_id',
#             relative_to_this_test_folder(
#                 'fixtures/studies/quads_f1_impala/data/pedigree'),
#             relative_to_this_test_folder(
#                 'fixtures/studies/quads_f1_impala/data/variants')
#         )

#     assert hdfs_parquet_files_config.files.pedigree == \
#         ['/tmp/test_data/study_id/pedigree/quads_f1_impala_pedigree.parquet']
#     assert hdfs_parquet_files_config.files.variants == [
#         '/tmp/test_data/study_id/variants/quads_f1_impala_variant_000001.'
#         'parquet'
#     ]
