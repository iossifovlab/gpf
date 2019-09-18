import pytest
import os

from dae.gpf_instance.gpf_instance import GPFInstance

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def mock_studies_manager(gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture(scope='function', autouse=True)
def replace_studies_manager(mocker, mock_studies_manager):
    mocker.patch('pheno_tool_api.views.get_studies_manager',
                 return_value=mock_studies_manager)
