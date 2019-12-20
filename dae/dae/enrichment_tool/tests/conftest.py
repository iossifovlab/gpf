import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.enrichment_tool.config import EnrichmentConfigParser
from dae.enrichment_tool.background import CodingLenBackground, \
    SamochaBackground


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def local_gpf_instance(gpf_instance):
    return gpf_instance(fixtures_dir())


@pytest.fixture(scope='session')
def variants_db_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


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
def background_facade(local_gpf_instance):
    return local_gpf_instance._background_facade
