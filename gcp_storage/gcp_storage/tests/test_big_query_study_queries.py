# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest

from dae.utils.regions import Region
from dae.studies.study import GenotypeDataStudy


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 2),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    (4, {"effect_types": ["missense"]}, 1),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_family_queries(
    imported_study: GenotypeDataStudy,
    index: int,
    query: dict[str, Any],
    ecount: int
) -> None:
    vs = list(imported_study.query_variants(**query))
    assert len(vs) == ecount


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 2),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    (4, {"effect_types": ["missense"]}, 1),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_summary_queries(
    imported_study: GenotypeDataStudy,
    index: int,
    query: dict[str, Any],
    ecount: int
) -> None:

    vs = list(imported_study.query_summary_variants(**query))

    assert len(vs) == ecount
