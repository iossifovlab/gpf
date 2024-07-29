# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from sqlglot import exp, parse_one, table
from sqlglot.executor import execute
from sqlglot.expressions import replace_placeholders
from sqlglot.schema import Schema, ensure_schema

from dae.query_variants.sql.schema2.sql_query_builder import (
    RealAttrFilterType,
    SqlBuilder,
)
from dae.utils.regions import Region

FAMILY_VARIANT_SCHEMA = {
    "bucket_index": "int",
    "summary_index": "int",
    "allele_index": "int",
    "sj_index": "int",
    "family_index": "int",
    "family_id": "string",
    "is_denovo": "tinyint",
    "allele_in_sexes": "tinyint",
    "allele_in_statuses": "tinyint",
    "allele_in_roles": "int",
    "inheritance_in_members": "smallint",
    "allele_in_members": "array<string>",
    "family_variant_data": "string",
    "region_bin": "string",
    "frequency_bin": "int",
    "coding_bin": "int",
    "family_bin": "int",
}

SUMMARY_ALLELE_SCHEMA = {
    "bucket_index": "int",
    "summary_index": "int",
    "allele_index": "int",
    "sj_index": "int",
    "chromosome": "string",
    "position": "int",
    "end_position": "int",
    "effect_gene": "array<struct<effect_gene_symbols:string,"
    "effect_types:string>>",
    "variant_type": "tinyint",
    "transmission_type": "tinyint",
    "reference": "string",
    "af_allele_count": "int",
    "af_allele_freq": "float",
    "af_parents_called": "int",
    "af_parents_freq": "float",
    "summary_variant_data": "string",
    "region_bin": "string",
    "frequency_bin": "int",
    "coding_bin": "int",
}

PEDIGREE_SCHEMA = {
    "family_id": "string",
    "person_id": "string",
    "dad_id": "string",
    "mom_id": "string",
    "sex": "tinyint",
    "status": "tinyint",
    "role": "int",
    "sample_id": "string",
    "generated": "boolean",
    "layout": "string",
    "not_sequenced": "boolean",
    "tag_multiplex_family": "string",
    "tag_simplex_family": "string",
    "tag_quad_family": "string",
    "tag_family_type": "string",
    "tag_affected_prb_family": "string",
    "tag_affected_mom_family": "string",
    "tag_missing_dad_family": "string",
    "tag_control_family": "string",
    "tags": "string",
    "tag_missing_mom_family": "string",
    "tag_affected_dad_family": "string",
    "tag_nuclear_family": "string",
    "tag_trio_family": "string",
    "tag_affected_sib_family": "string",
    "tag_family_type_full": "string",
    "member_index": "string",
    "tag_male_prb_family": "string",
    "tag_female_prb_family": "string",
}


@pytest.fixture()
def sql_schema() -> Schema:
    return ensure_schema(
        {
            "summary_table": SUMMARY_ALLELE_SCHEMA,
            "family_table": FAMILY_VARIANT_SCHEMA,
            "pedigree_table": PEDIGREE_SCHEMA,
        },
    )


@pytest.fixture()
def sql_builder(sql_schema: Schema) -> SqlBuilder:
    return SqlBuilder(sql_schema)


def test_summary_simple(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.summary_base()
    assert query is not None

    assert query.sql() == "SELECT * FROM summary_table AS sa"

    t = query.find(exp.Table)
    assert t is not None
    assert t.name == "summary_table"
    assert t.alias == "sa"

    t.replace(table("summary2"))
    assert query.sql() == "SELECT * FROM summary2"


def test_summary_replace_table(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.summary_base()
    q = exp.replace_tables(
        query,
        {"summary_table": "summary2"},
    )
    assert q.sql() == "SELECT * FROM summary2 AS sa /* summary_table */"


def test_family_variants(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.family_variants(
        sql_builder.summary_base(),
        sql_builder.family_base(),
    )
    assert query is not None

    assert query.sql() == (
        'WITH '
        '"summary" AS (SELECT * FROM "summary_table" AS "sa"), '
        '"family" AS (SELECT * FROM "family_table" AS "fa") '
        'SELECT * FROM "summary" AS "sa" JOIN "family" AS "fa" '
        'ON "fa"."sj_index" = "sa"."sj_index"'
    )


def test_region_bins_condition(sql_builder: SqlBuilder) -> None:
    rb = sql_builder.region_bins(
        ["chr1_0", "chr1_1"],
    )
    assert rb.sql() == ":region_bin IN ('chr1_0', 'chr1_1')"
    assert replace_placeholders(
        rb,
        region_bin=exp.to_column("sa.region_bin"),
    ).sql() == "sa.region_bin IN ('chr1_0', 'chr1_1')"


def test_regions_condition(sql_builder: SqlBuilder) -> None:
    regs = sql_builder.regions(
        [Region("chr1", 1, 10)],
    )
    assert regs.sql() == (
        ":chromosome = 'chr1' "
        "AND NOT (COALESCE(:end_position, :position) < 1 "
        "OR :position > 10)"
    )
    assert replace_placeholders(
        regs,
        chromosome=exp.to_column("fa.chromosome"),
        position=exp.to_column("fa.position"),
        end_position=exp.to_column("fa.end_position"),
    ).sql() == (
        "fa.chromosome = 'chr1' "
        "AND NOT (COALESCE(fa.end_position, fa.position) < 1 "
        "OR fa.position > 10)"
    )


def test_real_attr_filter_simple(sql_builder: SqlBuilder) -> None:
    raf = sql_builder._real_attr_filter(
        "attr1",
        (None, 1.0),
        is_frequency=False,
    )
    assert raf.sql() == "sa.attr1 <= 1.0"

    raf = sql_builder._real_attr_filter(
        "attr1",
        (None, 1.0),
        is_frequency=True,
    )
    assert raf.sql() == "sa.attr1 <= 1.0 OR sa.attr1 IS NULL"


def test_summary_effect_gene_base(sql_builder: SqlBuilder) -> None:
    query = sql_builder.summary_effect_gene_base()

    assert query.sql() == (
        "WITH summary_internal AS (SELECT * FROM summary_table AS sa), "
        "effect_gene_all AS (SELECT *, UNNEST(effect_gene) AS eg "
        "FROM summary_internal) "
        "SELECT * FROM effect_gene_all"
    )


def test_family_variants_with_effect_gene(sql_builder: SqlBuilder) -> None:
    query = sql_builder.family_variants(
        sql_builder.summary_effect_gene_base(),
        sql_builder.family_base(),
    )

    assert query.sql() == (
        'WITH '
        '"summary_internal" AS (SELECT * FROM "summary_table" AS "sa"), '
        '"effect_gene_all" AS ('
        'SELECT *, UNNEST("summary_internal"."effect_gene") AS "eg" '
        'FROM "summary_internal" AS "summary_internal"), '
        '"summary" AS (SELECT * FROM "effect_gene_all" AS "effect_gene_all"), '
        '"family" AS (SELECT * FROM "family_table" AS "fa") '
        'SELECT * FROM "summary" AS "sa" JOIN "family" AS "fa" '
        'ON "fa"."sj_index" = "sa"."sj_index"'
    )


@pytest.mark.parametrize(
    "regions,expected", [
        (None, 3),
        ([Region("chr1", 10, 20)], 1),
        ([Region("chr1", 12, 20)], 1),
        ([Region("chr1", 5, 12)], 1),
        ([Region("chr1", 49, 51)], 1),
        ([Region("chr1", 50, 51)], 1),
        ([Region("chr1", 49, 50)], 1),
        ([Region("chr1", 10, 30)], 2),
        ([Region("chr1", 10, 30), Region("chr1", 40, 50)], 3),
    ],
)
def test_summary_variants_regions_query(
    sql_builder: SqlBuilder,
    regions: list[Region],
    expected: int,
) -> None:
    tables = {
        "summary_table": [
            {"allele_index": 1, "chromosome": "chr1",
             "position": 11, "end_position": 13},
            {"allele_index": 1, "chromosome": "chr1",
             "position": 30, "end_position": 33},
            {"allele_index": 1, "chromosome": "chr1",
             "position": 50, "end_position": None},
        ],
    }
    query = sql_builder.summary_variants_query(regions=regions)
    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


@pytest.mark.parametrize(
    "real_attr_filter,expected", [
        ([("af_allele_freq", (0.0, 1.0))], 1),
        ([("af_allele_freq", (None, 1.0))], 1),
        ([("af_allele_freq", (0.5, None))], 2),
        ([("af_allele_freq", (None, None))], 2),
    ],
)
def test_summary_variants_real_attr_query(
    sql_builder: SqlBuilder,
    real_attr_filter: RealAttrFilterType,
    expected: int,
) -> None:
    tables = {
        "summary_table": [
            {"allele_index": 1, "af_allele_freq": 0.5},
            {"allele_index": 1, "af_allele_freq": None},
            {"allele_index": 1, "af_allele_freq": 50.0},

        ],
    }
    query = sql_builder.summary_variants_query(
        real_attr_filter=real_attr_filter,
    )

    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


@pytest.mark.parametrize(
    "frequency_filter,expected", [
        ([("af_allele_freq", (0.0, 1.0))], 1),
        ([("af_allele_freq", (None, 1.0))], 2),
        ([("af_allele_freq", (0.5, None))], 2),
        ([("af_allele_freq", (None, None))], 3),
    ],
)
def test_summary_variants_frequency_query(
    sql_builder: SqlBuilder,
    frequency_filter: RealAttrFilterType,
    expected: int,
) -> None:
    tables = {
        "summary_table": [
            {"allele_index": 1, "af_allele_freq": 0.5},
            {"allele_index": 1, "af_allele_freq": None},
            {"allele_index": 1, "af_allele_freq": 50.0},

        ],
    }
    query = sql_builder.summary_variants_query(
        frequency_filter=frequency_filter,
    )

    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


def test_build_ultra_rare_where(
    sql_builder: SqlBuilder,
) -> None:
    tables = {
        "summary_table": [
            {"allele_index": 1, "af_allele_count": 1},
            {"allele_index": 1, "af_allele_count": None},
            {"allele_index": 1, "af_allele_count": 50},

        ],
    }
    query = sql_builder.summary_variants_query(
        ultra_rare=True,
    )

    result = execute(
        query,
        tables=tables)

    assert len(result) == 2


@pytest.mark.parametrize(
    "attr,value_range,is_frequency,expected", [
        (
            "tt", (None, 1.0),
            True,
            "sa.tt <= 1.0 OR sa.tt IS NULL",
        ),
        (
            "tt", (None, 1.0),
            False,
            "sa.tt <= 1.0",
        ),
        (
            "tt", (0.0, 1.0),
            True,
            "sa.tt >= 0.0 AND sa.tt <= 1.0",
        ),
        (
            "tt", (0.0, 1.0),
            False,
            "sa.tt >= 0.0 AND sa.tt <= 1.0",
        ),
        (
            "tt", (0.0, None),
            True,
            "sa.tt >= 0.0",
        ),
        (
            "tt", (0.0, None),
            False,
            "sa.tt >= 0.0",
        ),
        (
            "tt", (None, None),
            True,
            "1 = 1",
        ),
        (
            "tt", (None, None),
            False,
            "NOT sa.tt IS NULL",
        ),
    ],
)
def test_real_attr_filter(
    attr: str,
    value_range: tuple[float | None, float | None],
    is_frequency: bool,  # noqa: FBT001
    expected: str,
    sql_builder: SqlBuilder,
) -> None:
    clause = sql_builder._real_attr_filter(
        attr,
        value_range,
        is_frequency=is_frequency,
    )
    assert clause.sql() == expected


@pytest.mark.xfail(reason="SQLGlot executor does not support UNNEST")
def test_sqlglot_nested_schema_experiments() -> None:
    tables = {
        "summary_table": [
            {"allele_index": 1, "chromosome": "chr1",
             "position": 11, "end_position": 13,
             "effect_gene": [
                 {"effect_gene_symbols": "A", "effect_types": "B"},
                 {"effect_gene_symbols": "C", "effect_types": "D"},
             ]},
            {"allele_index": 1, "chromosome": "chr1",
             "position": 30, "end_position": 33,
             "effect_gene": [
                 {"effect_gene_symbols": "E", "effect_types": "F"},
                 {"effect_gene_symbols": "G", "effect_types": "H"},
             ]},
            {"allele_index": 1, "chromosome": "chr1",
             "position": 50, "end_position": None,
             "effect_gene": [
                 {"effect_gene_symbols": "I", "effect_types": "J"},
                 {"effect_gene_symbols": "K", "effect_types": "L"},
             ]},
        ],
    }
    query = parse_one(
        """
        with
        effect_gene_all AS (
            SELECT *, UNNEST(effect_gene) as eg
            FROM summary_table as sa
        ),
        effect_gene AS (
            SELECT *
            FROM effect_gene_all
            WHERE
                eg.effect_gene_symbols = 'A'
        )
        select * from effect_gene
        """,
        dialect="duckdb",
    )

    assert query is not None
    result = execute(
        query,
        tables=tables)

    assert len(result) == 2
