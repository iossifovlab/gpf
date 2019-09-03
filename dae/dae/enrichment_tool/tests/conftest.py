import pytest

import os

from dae.configuration.dae_config_parser import DAEConfigParser
from dae.studies.variants_db import VariantsDb

from dae.enrichment_tool.config import EnrichmentConfigParser
from dae.enrichment_tool.background import CodingLenBackground, \
    SamochaBackground
from dae.enrichment_tool.background_facade import BackgroundFacade


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='session')
def f1_trio_enrichment_config(variants_db_fixture):
    return EnrichmentConfigParser.parse(
        variants_db_fixture.get_config('f1_trio'))


@pytest.fixture(scope='session')
def f1_trio(variants_db_fixture):
    return variants_db_fixture.get('f1_trio')


@pytest.fixture(scope='session')
def f1_trio_coding_len_background(f1_trio_enrichment_config):
    return CodingLenBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def f1_trio_samocha_background(f1_trio_enrichment_config):
    return SamochaBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def background_facade(variants_db_fixture):
    return BackgroundFacade(variants_db_fixture)
