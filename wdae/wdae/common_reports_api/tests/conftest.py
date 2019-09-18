import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def common_report_facade(gpf_instance):
    return gpf_instance.common_report_facade


@pytest.fixture(scope='module')
def use_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    common_report_facade.generate_all_common_reports()

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture()
def studies_manager(gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture()
def mock_studies_manager(db, mocker, studies_manager):
    mocker.patch(
        'common_reports_api.views.get_studies_manager',
        return_value=studies_manager)
