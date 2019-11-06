import pytest

from dae.backends.impala.tests.conftest import relative_to_this_test_folder


def test_get_data_dir(parquet_manager):
    assert parquet_manager.get_data_dir('study_id') == \
        relative_to_this_test_folder('fixtures/studies/study_id/data')


@pytest.mark.parametrize(
    'prefix,study_id,bucket_index,suffix,pedigree,variant', [
        (
            '/tmp', None, 0, None, '/tmp/pedigree/tmp_pedigree.parquet',
            '/tmp/variants/tmp_variant.parquet'
        ),
        (
            '/tmp', 'study_id', 0, None,
            '/tmp/pedigree/study_id_pedigree.parquet',
            '/tmp/variants/study_id_variant.parquet'
        ),
        (
            '/tmp', 'study_id', 1, None,
            '/tmp/pedigree/study_id_pedigree_000001.parquet',
            '/tmp/variants/study_id_variant_000001.parquet'
        ),
        (
            '/tmp', 'study_id', 0, 'suffix',
            '/tmp/pedigree/study_id_pedigreesuffix.parquet',
            '/tmp/variants/study_id_variantsuffix.parquet'
        ),
        (
            '/tmp', 'study_id', 1111111, 'suffix',
            '/tmp/pedigree/study_id_pedigree_1111111suffix.parquet',
            '/tmp/variants/study_id_variant_1111111suffix.parquet'
        )
    ]
)
def test_parquet_file_config(
        parquet_manager, prefix, study_id, bucket_index, suffix, pedigree,
        variant):
    parquet_file_config = parquet_manager.parquet_file_config(
        prefix, study_id, bucket_index, suffix
    )

    assert parquet_file_config.files.pedigree == pedigree
    assert parquet_file_config.files.variant == variant
