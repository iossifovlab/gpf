from __future__ import unicode_literals

import os
import pytest

from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb
