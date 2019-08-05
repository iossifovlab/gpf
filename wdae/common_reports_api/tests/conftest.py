import pytest

import os

from studies.factory import VariantsDb
from configuration.configuration import DAEConfig

from common_reports.common_report_facade import CommonReportFacade

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig.make_config(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def vdb_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='session')
def common_report_facade(vdb_fixture):
    common_report_facade = CommonReportFacade(vdb_fixture)

    return common_report_facade


@pytest.fixture(scope='module')
def use_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    common_report_facade.generate_all_common_reports()

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture()
def studies_manager(dae_config_fixture):
    return StudiesManager(dae_config_fixture)


@pytest.fixture()
def mock_studies_manager(db, mocker, studies_manager):
    studies_manager.reload_dataset()
    mocker.patch(
        'common_reports_api.views.get_studies_manager',
        return_value=studies_manager)
