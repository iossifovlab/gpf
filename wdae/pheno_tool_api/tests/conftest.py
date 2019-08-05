import pytest
import os
from configuration.configuration import DAEConfig
from studies.factory import VariantsDb
from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def mock_dae_config():
    return DAEConfig.make_config(fixtures_dir())


@pytest.fixture(scope='session')
def mock_vdb(mock_dae_config):
    return VariantsDb(mock_dae_config)


@pytest.fixture(scope='session')
def mock_studies_manager(mock_dae_config):
    return StudiesManager(mock_dae_config)


@pytest.fixture(scope='function', autouse=True)
def replace_studies_manager(mocker, mock_studies_manager):
    mocker.patch('pheno_tool_api.views.get_studies_manager',
                 return_value=mock_studies_manager)
