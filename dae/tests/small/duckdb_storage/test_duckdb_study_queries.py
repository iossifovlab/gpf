# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.duckdb_storage.duckdb_variants import DuckDbVariants
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def duckdb_backend(imported_study: GenotypeData) -> DuckDbVariants:
    return cast(DuckDbVariants, imported_study._backend)  # type: ignore


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
])
def test_family_queries(
        duckdb_backend: DuckDbVariants,
        query: dict, ecount: int) -> None:
    vs = list(duckdb_backend.query_variants(**query))
    assert len(vs) == ecount


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
])
def test_summary_queries(
        duckdb_backend: DuckDbVariants,
        query: dict, ecount: int) -> None:
    vs = list(duckdb_backend.query_summary_variants(**query))
    assert len(vs) == ecount
