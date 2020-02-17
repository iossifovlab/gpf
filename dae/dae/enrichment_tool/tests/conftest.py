import pytest

from dae.enrichment_tool.background import CodingLenBackground, \
    SamochaBackground


@pytest.fixture(scope='session')
def f1_trio_enrichment_config(variants_db_fixture):
    return variants_db_fixture.get_config('f1_trio').enrichment


@pytest.fixture(scope='session')
def f1_trio(variants_db_fixture):
    result = variants_db_fixture.get('f1_trio')
    return result


@pytest.fixture(scope='session')
def f1_trio_coding_len_background(f1_trio_enrichment_config):
    return CodingLenBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def f1_trio_samocha_background(f1_trio_enrichment_config):
    return SamochaBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def background_facade(fixtures_gpf_instance):
    return fixtures_gpf_instance._background_facade
