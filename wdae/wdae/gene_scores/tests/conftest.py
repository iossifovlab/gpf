from typing import cast
import pytest
from dae.gene_scores.gene_scores import GeneScoresDb
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="session")
def gene_scores_db(fixtures_gpf_instance: GPFInstance) -> GeneScoresDb:
    return cast(GeneScoresDb, fixtures_gpf_instance.gene_scores_db)
