import os
import pytest

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.weights import WeightsFactory

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def dae_config_fixture():
    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
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
        'gene_weights.tests.test_gene_weights_factory.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture()
def weights_factory(dae_config_fixture):
    gene_info_config = GeneInfoConfigParser.read_and_parse_file_configuration(
        dae_config_fixture.gene_info_db.conf_file,
        dae_config_fixture.dae_data_dir
    )
    weights_factory = WeightsFactory(config=gene_info_config.gene_weights)

    return weights_factory
