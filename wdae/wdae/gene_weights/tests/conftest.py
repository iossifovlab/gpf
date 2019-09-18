import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def dae_config_fixture(gpf_instance):
    return gpf_instance.dae_config


@pytest.fixture(scope='function')
def studies_manager(gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture(scope='function')
def mock_studies_manager(db, mocker, studies_manager):
    mocker.patch(
        'gene_weights.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'gene_weights.tests.test_gene_weights_factory.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture(scope='function')
def weights_factory(gpf_instance):
    return gpf_instance.weights_factory
