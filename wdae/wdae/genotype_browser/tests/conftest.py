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
def studies_manager(db, gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture(scope='function')
def mock_studies_manager(mocker, studies_manager):
    mocker.patch(
        'genotype_browser.views.get_studies_manager',
        return_value=studies_manager)
