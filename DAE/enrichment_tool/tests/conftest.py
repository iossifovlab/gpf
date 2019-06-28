import pytest

import os

from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb

from enrichment_tool.config import EnrichmentConfig


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='session')
def enrichment_config(variants_db_fixture):
    return EnrichmentConfig.from_config(
        variants_db_fixture.get_config('quads_f1'))
