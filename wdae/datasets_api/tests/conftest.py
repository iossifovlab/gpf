import os
import pytest

from configurable_entities.configuration import DAEConfig
from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def dae_config_fixture():
    dae_config = DAEConfig.make_config(fixtures_dir())
    return dae_config


@pytest.fixture()
def studies_manager(dae_config_fixture):
    return StudiesManager(dae_config_fixture)


@pytest.fixture()
def mock_studies_manager(db, mocker, studies_manager):
    studies_manager.reload_dataset()
    mocker.patch(
        'datasets_api.views.get_studies_manager',
        return_value=studies_manager)
