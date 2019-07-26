import os
import pytest

from configurable_entities.configuration import DAEConfig
from datasets_api.studies_manager import StudiesManager

from gene.config import GeneInfoConfig
from gene.weights import WeightsLoader


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture()
def studies_manager(dae_config_fixture):
    return StudiesManager(dae_config_fixture)


@pytest.fixture()
def mock_studies_manager(db, mocker, studies_manager):
    studies_manager.reload_dataset()

    mocker.patch(
        'gene_weights.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'gene_weights.tests.test_gene_weights_loader.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture()
def weights_loader(dae_config_fixture):
    gene_info_config = GeneInfoConfig.from_config(dae_config_fixture)
    weights_loader = WeightsLoader(config=gene_info_config)

    return weights_loader
