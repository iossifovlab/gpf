from __future__ import unicode_literals

import os
import pytest

from django.test import Client

from datasets_api.studies_manager import StudiesManager
from configurable_entities.configuration import DAEConfig


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def client(mocker, dae_config_fixture):
    mocker.patch('datasets_api.views.get_studies_manager',
                 side_effect=lambda: StudiesManager(dae_config_fixture))
    return Client()


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config
