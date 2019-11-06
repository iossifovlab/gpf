from dae.backends.impala.tests.conftest import relative_to_this_test_folder


def test_get_data_dir(parquet_manager):
    assert parquet_manager.get_data_dir('study_id') == \
        relative_to_this_test_folder('fixtures/studies/study_id/data')
