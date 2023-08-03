import pytest

from dae.enrichment_tool.background import \
    CodingLenBackground, \
    SamochaBackground


@pytest.fixture(scope="session")
def f1_trio_enrichment_config(fixtures_gpf_instance):
    return fixtures_gpf_instance.get_genotype_data_config("f1_trio").enrichment


@pytest.fixture(scope="session")
def f1_trio(fixtures_gpf_instance):
    result = fixtures_gpf_instance.get_genotype_data("f1_trio")
    return result


@pytest.fixture(scope="session")
def f1_trio_coding_len_background(f1_trio_enrichment_config):
    return CodingLenBackground(f1_trio_enrichment_config)


@pytest.fixture(scope="session")
def f1_trio_samocha_background(f1_trio_enrichment_config):
    return SamochaBackground(f1_trio_enrichment_config)


@pytest.fixture(scope="session")
def background_facade(fixtures_gpf_instance):
    return fixtures_gpf_instance._background_facade
