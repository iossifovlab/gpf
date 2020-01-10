import pytest


@pytest.fixture(scope='session')
def gene_weights_db(fixtures_gpf_instance):
    return fixtures_gpf_instance.gene_weights_db
