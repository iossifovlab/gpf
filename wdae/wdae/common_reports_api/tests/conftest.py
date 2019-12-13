import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def common_report_facade(gpf_instance):
    return gpf_instance._common_report_facade


@pytest.fixture(scope='session')
def use_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    common_report_facade.generate_common_report('Study1')
    common_report_facade.generate_common_report('study4')

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance._variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
