# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

import pytest
from dae.duckdb_storage.duckdb2_variants import DuckDb2Variants
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.query_variants.sql.schema2.sql_query_builder import (
    SqlQueryBuilder,
    TagsQuery,
)
from dae.studies.study import GenotypeDataStudy
from dae.utils.regions import Region


@pytest.fixture
def t4c8_storage_registry(
    t4c8_instance: GPFInstance,
) -> GenotypeStorageRegistry:
    return cast(GenotypeStorageRegistry, t4c8_instance.genotype_storages)


@pytest.fixture
def duckdb2_variants(t4c8_study_2: GenotypeDataStudy) -> DuckDb2Variants:
    return cast(DuckDb2Variants, t4c8_study_2.backend)


@pytest.fixture
def query_builder(
    duckdb2_variants: DuckDb2Variants,
) -> SqlQueryBuilder:
    return duckdb2_variants.query_builder


@pytest.mark.parametrize("params, coding_bin", [
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 1),
    ({"effect_types": ["intergenic"]}, None),
    ({"effect_types": ["intergenic", "synonymous"]}, None),
    ({}, None),
])
def test_coding_bin_heuristics_query(
    params: dict[str, Any],
    coding_bin: int | None,
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_summary_variants_query(**params)
        assert queries is not None
        assert len(queries) > 0
        query = queries[0]

        if coding_bin is None:
            assert "coding_bin" not in query
        else:
            assert f"sa.coding_bin = {coding_bin}" in query


@pytest.mark.parametrize("params, region_bins", [
    ({"regions": [Region("chr1", 2, 20)]}, ["chr1_0"]),
    ({"regions": [Region("chr1", 2, 120)]}, ["chr1_0", "chr1_1"]),
    ({"regions": [Region("chr1")]}, ["chr1_0", "chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", 105)]}, ["chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", None, 105)]}, ["chr1_0", "chr1_1"]),
])
def test_region_bin_heuristics_query(
    params: dict[str, Any],
    region_bins: list[str] | None,
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_summary_variants_query(**params)
        assert queries is not None
        assert len(queries) > 0
        query = queries[0]

        if region_bins is None:
            assert "region_bin" not in query
        else:
            assert "sa.region_bin" in query
            for region_bin in region_bins:
                assert f"'{region_bin}'" in query


@pytest.mark.parametrize("params, frequency_bins", [
    ({"ultra_rare": True}, "(0, 1)"),
    ({"ultra_rare": False}, None),
    ({}, None),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.1))]}, None),
    ({"frequency_filter": [("gnomad_af", (None, 100.0))]}, None),
    ({"ultra_rare": True, "frequency_filter": [("gnomad_af", (None, 100.0))]},
     "(0, 1)"),
    ({"ultra_rare": False, "frequency_filter": [("gnomad_af", (None, 100.0))]},
     None),
])
def test_frequency_bin_heuristics_query(
    params: dict[str, Any],
    frequency_bins: str | None,
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_summary_variants_query(**params)
        assert queries is not None
        assert len(queries) > 0
        query = queries[0]

        if frequency_bins is None:
            assert "frequency_bin" not in query
        else:
            assert "sa.frequency_bin" in query
            assert f"sa.frequency_bin IN {frequency_bins}" in query


@pytest.mark.parametrize("params, coding_bin", [
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 1),
    ({"effect_types": ["intergenic"]}, None),
    ({"effect_types": ["intergenic", "synonymous"]}, None),
    ({}, None),
])
def test_coding_bin_heuristics_family_query(
    params: dict[str, Any],
    coding_bin: int | None,
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_family_variants_query(**params)
        assert queries is not None
        assert len(queries) > 0
        query = queries[0]

        if coding_bin is None:
            assert "coding_bin" not in query
        else:
            assert f"sa.coding_bin = {coding_bin}" in query
            assert f"fa.coding_bin = {coding_bin}" in query


@pytest.mark.parametrize("params, count, region_bins", [
    ({"regions": [Region("chr1", 2, 20)]}, 1, ["chr1_0"]),
    ({"regions": [Region("chr1", 2, 120)]}, 1, ["chr1_0", "chr1_1"]),
    ({"regions": [Region("chr1")]}, 1, ["chr1_0", "chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", 105)]}, 1, ["chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", None, 105)]}, 1, ["chr1_0", "chr1_1"]),
    ({"regions": None}, 3, ["chr1_0"]),
])
def test_region_bin_heuristics_family_query(
    params: dict[str, Any],
    count: int,
    region_bins: list[str],
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_family_variants_query(**params)
        assert queries is not None
        assert len(queries) == count
        query = queries[0]

        assert "sa.region_bin" in query
        assert "fa.region_bin" in query
        for region_bin in region_bins:
            assert f"'{region_bin}'" in query


def test_region_bin_heuristics_batched_query(
    query_builder: SqlQueryBuilder,
) -> None:

    queries = query_builder.build_family_variants_query()

    assert queries is not None
    assert len(queries) == 3
    for query in queries:
        assert "sa.region_bin" in query
        assert "fa.region_bin" in query


@pytest.mark.parametrize("params, frequency_bins", [
    ({"ultra_rare": True}, "(0, 1)"),
    ({"ultra_rare": False}, None),
    ({}, None),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.1))]}, None),
])
def test_frequency_bin_heuristics_family_query(
    params: dict[str, Any],
    frequency_bins: str | None,
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_family_variants_query(**params)
        assert queries is not None
        assert len(queries) > 0
        query = queries[0]

        if frequency_bins is None:
            assert "frequency_bin" not in query
        else:
            assert "sa.frequency_bin" in query
            assert "fa.frequency_bin" in query
            assert f"fa.frequency_bin IN {frequency_bins}" in query


def test_duckdb2_variants_simple(
    t4c8_storage_registry: GenotypeStorageRegistry,
    t4c8_study_2: GenotypeDataStudy,
) -> None:

    svs = list(t4c8_storage_registry.query_summary_variants(
        [t4c8_study_2.study_id], {}))
    assert len(svs) == 6

    fvs = list(t4c8_storage_registry.query_variants(
        [(t4c8_study_2.study_id, {})]))
    assert len(fvs) == 12


@pytest.mark.parametrize("params, region_bins, region_borders", [
    ({"genes": ["t4"]}, {"chr1_0"}, {5, 85}),
    ({"genes": ["c8"]}, {"chr1_0", "chr1_1", "chr1_2"}, {100, 205}),
])
def test_gene_regions_heuristics_summary_query(
    params: dict[str, Any],
    region_bins: set[str],
    region_borders: set[int],
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_summary_variants_query(**params)
        assert queries is not None
        assert len(queries) == 1

        query = queries[0]

        assert "sa.chromosome" in query
        assert "sa.position" in query
        assert "sa.end_position" in query

        assert "sa.region_bin" in query
        for region_bin in region_bins:
            assert f"'{region_bin}'" in query
        for border in region_borders:
            assert f"{border}" in query


@pytest.mark.parametrize("params, region_bins, region_borders", [
    ({"genes": ["t4"]}, {"chr1_0"}, {5, 85}),
    ({"genes": ["c8"]}, {"chr1_0", "chr1_1", "chr1_2"}, {100, 205}),
])
def test_gene_regions_heuristics_family_query(
    params: dict[str, Any],
    region_bins: set[str],
    region_borders: set[int],
    query_builder: SqlQueryBuilder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as m:
        m.setattr(query_builder, "GENE_REGIONS_HEURISTIC_EXTEND", 0)
        assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
        queries = query_builder.build_family_variants_query(**params)
        assert queries is not None
        assert len(queries) == 1

        query = queries[0]

        assert "sa.chromosome" in query
        assert "sa.position" in query
        assert "sa.end_position" in query

        assert "sa.region_bin" in query
        for region_bin in region_bins:
            assert f"'{region_bin}'" in query
        for border in region_borders:
            assert f"{border}" in query


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 2),
    ({"genes": ["c8"]}, 5),
    ({"effect_types": ["missense"]}, 2),
    ({"effect_types": ["synonymous"]}, 4),
    ({"regions": [Region("chr1")]}, 12),
    ({"regions": [Region("chr1", None, 55)]}, 4),
    ({"regions": [Region("chr1", 55, None)]}, 8),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 12),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 9),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 8),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_family_variants_counting(
    params: dict[str, Any],
    count: int,
    t4c8_storage_registry: GenotypeStorageRegistry,
    t4c8_study_2: GenotypeDataStudy,
) -> None:
    fvs = list(t4c8_storage_registry.query_variants(
        [(t4c8_study_2.study_id, params)]))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 3),
    ({"regions": [Region("chr1")]}, 6),
    ({"regions": [Region("chr1", None, 55)]}, 2),
    ({"regions": [Region("chr1", 55, None)]}, 4),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 6),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 5),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 4),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_summary_variants_counting(
    params: dict[str, Any],
    count: int,
    t4c8_storage_registry: GenotypeStorageRegistry,
    t4c8_study_2: GenotypeDataStudy,
) -> None:
    svs = list(t4c8_storage_registry.query_summary_variants(
        [t4c8_study_2.study_id], params))
    assert len(svs) == count


@pytest.mark.parametrize(
    "params,expected", [
        (
            {
                "roles": "( prb and not sib ) or ( prb and sib )",
                "inheritance": [
                    "not possible_denovo and not possible_omission",
                    "any([denovo,mendelian,missing,omission])",
                ],
                "ultra_rare": True,
            },
            ["0", "1"],
        ),
        (
            {
                "roles": "( prb and not sib ) or ( prb and sib )",
                "inheritance": [
                    "not possible_denovo and not possible_omission",
                    "any([denovo,mendelian,missing,omission])",
                ],
                "ultra_rare": False,
                "frequency_filter": [("af_allele_freq", (None, 1.0))],
            },
            ["0", "1", "2"],
        ),
    ],
)
def test_calc_frequency_bin_heuristics(
    params: dict[str, Any],
    expected: list[str],
    query_builder: SqlQueryBuilder,
) -> None:
    frequency_bins = query_builder.calc_frequency_bins(**params)
    assert frequency_bins == expected


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"variant_type": "sub"}, 10),
    ({"variant_type": "ins"}, 5),
    ({"variant_type": "del"}, 0),
])
def test_query_family_variants_by_variant_type(
    params: dict[str, Any],
    count: int,
    t4c8_storage_registry: GenotypeStorageRegistry,
    t4c8_study_2: GenotypeDataStudy,
) -> None:
    fvs = list(t4c8_storage_registry.query_variants(
        [(t4c8_study_2.study_id, params)]))
    assert len(fvs) == count


@pytest.mark.no_gs_impala
def test_sj_index(
    query_builder: SqlQueryBuilder,
) -> None:
    assert "sj_index" in query_builder.schema.column_names("summary_table")
    assert "sj_index" in query_builder.schema.column_names("family_table")


def test_pedigree_schema(
    duckdb2_variants: DuckDb2Variants,
) -> None:
    pedigree_columns = duckdb2_variants.query_builder.schema.column_names(
        "pedigree_table",
    )
    assert pedigree_columns
    assert "family_id" in pedigree_columns
    assert "person_id" in pedigree_columns
    assert "family_bin" in pedigree_columns
    assert "tag_simplex_family" in pedigree_columns
    assert "tag_multiplex_family" in pedigree_columns


@pytest.mark.parametrize("params, count", [
    ({"tags_query": TagsQuery(selected_family_tags=["tag_trio_family"])}, 12),
    ({"tags_query": TagsQuery(selected_family_tags=["tag_quad_family"])}, 0),
    ({"tags_query": TagsQuery(deselected_family_tags=["tag_trio_family"])}, 0),
    (
        {"tags_query": TagsQuery(deselected_family_tags=["tag_quad_family"])},
        12,
    ),
    (
        {
            "tags_query": TagsQuery(selected_family_tags=["tag_trio_family"]),
            "person_ids": ["ch1", "ch3"],
        }, 9,
    ),
])
def test_family_tag_queries_working(
    params: dict[str, Any],
    count: int,
    t4c8_storage_registry: GenotypeStorageRegistry,
    t4c8_study_2: GenotypeDataStudy,
) -> None:
    fvs = list(t4c8_storage_registry.query_variants(
        [((t4c8_study_2.study_id, params))]))
    assert len(fvs) == count
