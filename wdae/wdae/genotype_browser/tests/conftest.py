import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets
from dae_conftests.dae_conftests import get_global_dae_fixtures_dir


def fixtures_dir():
    return get_global_dae_fixtures_dir()


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    print('otumeel says: ', fixtures_dir())
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance._variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
