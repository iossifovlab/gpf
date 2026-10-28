# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from gain.utils.regions import Region

from gpf.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from gpf.studies.study import GenotypeData

QUOTED_CHROM = "nope' OR '1'='1"
# The storage filters the region in Python after the SQL query, so only the
# categorical filter proves the escaping of the SQL literal end to end.
QUOTED_VALUE = "x' OR '1'='1"


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
    ({"regions": [Region(QUOTED_CHROM)]}, 0),
    ({"categorical_attr_filter": [("chromosome", [QUOTED_VALUE])]}, 0),
])
def test_family_queries(
        imported_study: GenotypeData,
        foobar_storage_registry: GenotypeStorageRegistry,
        query: dict, ecount: int) -> None:
    vs = list(
        foobar_storage_registry.query_variants(
            [(imported_study.study_id, query)],
        ),
    )
    assert len(vs) == ecount


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
    ({"regions": [Region(QUOTED_CHROM)]}, 0),
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
