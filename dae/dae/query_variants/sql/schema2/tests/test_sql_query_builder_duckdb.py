# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

import pytest

from dae.duckdb_storage.duckdb2_variants import DuckDb2Variants
from dae.query_variants.sql.schema2.sql_query_builder import (
    SqlQueryBuilder2,
)
from dae.studies.study import GenotypeData
from dae.utils.regions import Region


@pytest.fixture()
def duckdb2_variants(
    t4c8_study_1: GenotypeData,
) -> DuckDb2Variants:
    duckdb_variants = cast(
        DuckDb2Variants,
        t4c8_study_1._backend,  # type: ignore
    )
    duckdb_variants.query_builder.GENE_REGIONS_HEURISTIC_EXTEND = 0
    return duckdb_variants


@pytest.fixture()
def query_builder(
    duckdb2_variants: DuckDb2Variants,
) -> SqlQueryBuilder2:
    sql_query_builder = duckdb2_variants.query_builder
    assert sql_query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    return sql_query_builder


@pytest.mark.parametrize("params, count", [
    ({"regions": [Region("chr1")]}, 3),
    ({"regions": [Region("chr1", None, 55)]}, 1),
    ({"regions": [Region("chr1", 55, None)]}, 2),
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 2),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 3),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 3),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 1),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 1),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 1),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"variant_type": "sub"}, 3),
    ({"variant_type": "ins"}, 0),
    ({"variant_type": "del"}, 0),
    ({"variant_type": "sub or del"}, 3),
])
def test_query_summary_variants_counting(
    params: dict[str, Any],
    count: int,
    duckdb2_variants: DuckDb2Variants,
) -> None:
    svs = list(duckdb2_variants.query_summary_variants(**params))
    assert len(svs) == count


@pytest.mark.parametrize("params, count", [
    ({"regions": [Region("chr1")]}, 4),
    ({"regions": [Region("chr1", None, 55)]}, 1),
    ({"regions": [Region("chr1", 55, None)]}, 3),
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 2),
    ({"effect_types": ["synonymous"]}, 3),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 3),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 4),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 3),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 2),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"variant_type": "sub"}, 4),
    ({"variant_type": "ins"}, 0),
    ({"variant_type": "del"}, 0),
    ({"variant_type": "sub or del"}, 4),
])
def test_query_family_variants_counting(
    params: dict[str, Any],
    count: int,
    duckdb2_variants: DuckDb2Variants,
) -> None:
    fvs = list(duckdb2_variants.query_variants(**params))
    assert len(fvs) == count
