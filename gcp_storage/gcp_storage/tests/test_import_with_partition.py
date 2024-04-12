# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast, Any

import pytest

from dae.utils.regions import Region
from dae.studies.study import GenotypeDataStudy
from gcp_storage.bigquery_variants import BigQueryVariants


@pytest.fixture(scope="session")
def bq_backend(partition_study: GenotypeDataStudy) -> BigQueryVariants:
    return cast(BigQueryVariants, partition_study._backend)


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 8),
    (2, {"genes": ["g1"]}, 4),
    (3, {"genes": ["g2"]}, 4),
    (4, {"effect_types": ["missense"]}, 4),
    (5, {"effect_types": ["splice-site"]}, 2),
    (6, {"regions": [Region("foo", 10, 10)]}, 2),
])
def test_family_queries(
    bq_backend: BigQueryVariants,
    index: int,
    query: dict[str, Any],
    ecount: int
) -> None:
    vs = list(bq_backend.query_variants(**query))
    assert len(vs) == ecount


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 4),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 2),
    (4, {"effect_types": ["missense"]}, 2),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_summary_queries(
    bq_backend: BigQueryVariants,
    index: int,
    query: dict[str, Any],
    ecount: int
) -> None:

    vs = list(bq_backend.query_summary_variants(**query))

    assert len(vs) == ecount
