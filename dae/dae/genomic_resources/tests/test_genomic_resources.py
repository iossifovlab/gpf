import pytest

from dae.genomic_resources.resource_db import GenomicResourceDB
from dae.genomic_resources.score_resources import NPScoreResource, \
    PositionScoreResource


@pytest.fixture
def test_grdb(test_grdb_config):
    grdb = GenomicResourceDB(
        test_grdb_config["genomic_resource_repositories"])
    assert len(grdb.repositories) == 1

    return grdb


def test_np_score_resource_type(test_grdb):

    resource = test_grdb.get_resource("hg19/MPC")
    assert resource is not None

    assert isinstance(resource, NPScoreResource)


def test_position_score_resource_type(test_grdb):

    resource = test_grdb.get_resource("hg19/phastCons100")
    assert resource is not None

    assert isinstance(resource, PositionScoreResource)
