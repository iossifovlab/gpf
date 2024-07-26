# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from sqlglot import exp, table
from sqlglot.expressions import replace_placeholders

from dae.query_variants.sql.schema2.sql_query_builder import (
    SqlBuilder,
)
from dae.utils.regions import Region


@pytest.fixture()
def sql_builder() -> SqlBuilder:
    return SqlBuilder()


def test_summary_simple(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.summary_base()
    assert query is not None

    assert query.sql() == "SELECT * FROM summary AS sa"

    t = query.find(exp.Table)
    assert t is not None
    assert t.name == "summary"
    assert t.alias == "sa"

    t.replace(table("summary2"))
    assert query.sql() == "SELECT * FROM summary2"


def test_summary_replace_table(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.summary_base()
    q = exp.replace_tables(
        query,
        {"summary": "summary2"},
    )
    assert q.sql() == "SELECT * FROM summary2 AS sa /* summary */"


def test_family_variants(sql_builder: SqlBuilder) -> None:
    assert sql_builder is not None
    query = sql_builder.family_variants(
        sql_builder.summary_base(),
        sql_builder.family_base(),
    )
    assert query is not None

    assert query.sql() == (
        "WITH summary AS (SELECT * FROM summary AS sa), "
        "family AS (SELECT * FROM family AS fa) "
        "SELECT * FROM summary AS sa JOIN family AS fa "
        "ON sa.sj_index = fa.sj_index"
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


def test_real_attr_filter(sql_builder: SqlBuilder) -> None:
    raf = sql_builder._real_attr_filter(
        "attr1",
        (None, 1.0),
        is_frequency=False,
    )
    assert raf.sql() == ":attr1 <= 1.0"
    assert replace_placeholders(
        raf,
        attr1=exp.to_column("sa.attr1"),
    ).sql() == "sa.attr1 <= 1.0"

    raf = sql_builder._real_attr_filter(
        "attr1",
        (None, 1.0),
        is_frequency=True,
    )
    assert raf.sql() == ":attr1 <= 1.0 OR :attr1 IS NULL"
