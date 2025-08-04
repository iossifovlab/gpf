# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.studies.study import GenotypeData


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
])
def test_family_queries(
        imported_study: GenotypeData,
        foobar_storage_registry: GenotypeStorageRegistry,
        query: dict, ecount: int) -> None:
    vs = list(
        foobar_storage_registry.query_variants(
            [imported_study.study_id], query,
        ),
    )
    assert len(vs) == ecount


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
])
def test_summary_queries(
        imported_study: GenotypeData,
        foobar_storage_registry: GenotypeStorageRegistry,
        query: dict, ecount: int) -> None:
    vs = list(
        foobar_storage_registry.query_summary_variants(
            [imported_study.study_id], query,
        ),
    )
    assert len(vs) == ecount
