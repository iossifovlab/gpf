import pytest


@pytest.fixture(scope="session")
def gene_scores_db(fixtures_gpf_instance):
    return fixtures_gpf_instance.gene_scores_db
