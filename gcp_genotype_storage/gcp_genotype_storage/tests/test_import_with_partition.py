# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

# from dae.utils.regions import Region


@pytest.fixture(scope="session")
def bq_backend(partition_study):
    return partition_study._backend


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 8),
])
def test_family_queries(bq_backend, index, query, ecount):
    vs = list(bq_backend.query_variants(**query))
    assert len(vs) == ecount
