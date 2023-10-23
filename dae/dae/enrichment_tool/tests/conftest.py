# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from box import Box

from dae.enrichment_tool.background import \
    CodingLenBackground, \
    SamochaBackground
from dae.enrichment_tool.background_facade import BackgroundFacade
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


@pytest.fixture(scope="session")
def f1_trio_enrichment_config(fixtures_gpf_instance: GPFInstance) -> Box:
    config = fixtures_gpf_instance.get_genotype_data_config("f1_trio")
    assert config is not None

    return cast(Box, config["enrichment"])


@pytest.fixture(scope="session")
def f1_trio(fixtures_gpf_instance: GPFInstance) -> GenotypeData:
    result = fixtures_gpf_instance.get_genotype_data("f1_trio")
    return result


@pytest.fixture(scope="session")
def f1_trio_coding_len_background(
    f1_trio_enrichment_config: Box
) -> CodingLenBackground:
    return CodingLenBackground(f1_trio_enrichment_config)


@pytest.fixture(scope="session")
def f1_trio_samocha_background(
    f1_trio_enrichment_config: Box
) -> SamochaBackground:
    return SamochaBackground(f1_trio_enrichment_config)


@pytest.fixture(scope="session")
def background_facade(fixtures_gpf_instance: GPFInstance) -> BackgroundFacade:
    return fixtures_gpf_instance._background_facade
