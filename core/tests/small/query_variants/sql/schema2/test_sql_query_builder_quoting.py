# pylint: disable=C0114,C0116,W0212
from collections.abc import Callable

import pytest
from gain.utils.regions import Region
from sqlglot import exp, parse_one

from gpf.query_variants.sql.schema2.sql_query_builder import SqlQueryBuilder

QUOTED = "o'brien"


def _parse(cond: exp.Expression) -> exp.Expression:
    return parse_one(cond.sql())


def test_genes_one_value_with_quote_is_one_literal() -> None:
    parsed = _parse(SqlQueryBuilder.genes([QUOTED]))

    assert isinstance(parsed, exp.EQ)
    assert parsed.left.sql() == "eg.effect_gene_symbols"
    assert isinstance(parsed.right, exp.Literal)
    assert parsed.right.is_string
    assert parsed.right.this == QUOTED


def _assert_in_literals(
    parsed: exp.Expression, column: str, values: list[str],
) -> None:
    assert isinstance(parsed, exp.In)
    assert parsed.this.sql() == column
    items = parsed.expressions
    assert all(
        isinstance(item, exp.Literal) and item.is_string for item in items)
    assert [item.this for item in items] == values


def test_genes_two_values_with_quote_are_two_literals() -> None:
    parsed = _parse(SqlQueryBuilder.genes([QUOTED, "c8"]))

    _assert_in_literals(parsed, "eg.effect_gene_symbols", [QUOTED, "c8"])


def _assert_eq_literal(
    parsed: exp.Expression, column: str, value: str,
) -> None:
    assert isinstance(parsed, exp.EQ)
    assert parsed.left.sql() == column
    assert isinstance(parsed.right, exp.Literal)
    assert parsed.right.is_string
    assert parsed.right.this == value


def test_family_ids_one_value_with_quote_is_one_literal() -> None:
    parsed = _parse(SqlQueryBuilder.family_ids([QUOTED]))

    _assert_eq_literal(parsed, "fa.family_id", QUOTED)


def test_family_ids_two_values_with_quote_are_two_literals() -> None:
    parsed = _parse(SqlQueryBuilder.family_ids([QUOTED, "f1"]))

    _assert_in_literals(parsed, "fa.family_id", [QUOTED, "f1"])


def test_person_ids_one_value_with_quote_is_one_literal() -> None:
    parsed = _parse(SqlQueryBuilder.person_ids([QUOTED]))

    _assert_eq_literal(parsed, "fa.aim", QUOTED)


def test_person_ids_two_values_with_quote_are_two_literals() -> None:
    parsed = _parse(SqlQueryBuilder.person_ids([QUOTED, "ch1"]))

    _assert_in_literals(parsed, "fa.aim", [QUOTED, "ch1"])


def test_categorical_attr_filter_value_with_quote_is_one_literal() -> None:
    parsed = _parse(
        SqlQueryBuilder._categorical_attr_filter("gene_effect", [QUOTED]))

    _assert_eq_literal(parsed, "sa.gene_effect", QUOTED)


def test_categorical_attr_filter_two_values_with_quote() -> None:
    parsed = _parse(SqlQueryBuilder._categorical_attr_filter(
        "gene_effect", [QUOTED, "lgd"]))

    assert isinstance(parsed, exp.Or)
    _assert_eq_literal(parsed.left, "sa.gene_effect", QUOTED)
    _assert_eq_literal(parsed.right, "sa.gene_effect", "lgd")


@pytest.mark.parametrize("region", [
    Region(QUOTED),
    Region(QUOTED, None, 55),
    Region(QUOTED, 55, None),
    Region(QUOTED, 55, 100),
])
def test_region_chromosome_with_quote_is_one_literal(region: Region) -> None:
    parsed = _parse(SqlQueryBuilder.regions([region]))

    chrom_conditions = [
        eq for eq in parsed.find_all(exp.EQ)
        if isinstance(eq.left, exp.Placeholder)
    ]
    assert len(chrom_conditions) == 1
    _assert_eq_literal(chrom_conditions[0], ":chromosome", QUOTED)


def test_effect_types_two_values_with_quote_are_two_literals() -> None:
    parsed = _parse(SqlQueryBuilder.effect_types([QUOTED, "missense"]))

    _assert_in_literals(parsed, "eg.effect_types", [QUOTED, "missense"])


@pytest.mark.parametrize("method, values, expected", [
    (SqlQueryBuilder.genes, ["t4"], "eg.effect_gene_symbols = 't4'"),
    (
        SqlQueryBuilder.genes, ["t4", "c8"],
        "eg.effect_gene_symbols IN ('t4', 'c8')",
    ),
    (SqlQueryBuilder.family_ids, ["f1"], "fa.family_id = 'f1'"),
    (
        SqlQueryBuilder.family_ids, ["f1", "f2"],
        "fa.family_id IN ('f1', 'f2')",
    ),
    (SqlQueryBuilder.person_ids, ["ch1"], "fa.aim = 'ch1'"),
    (SqlQueryBuilder.person_ids, ["ch1", "ch3"], "fa.aim IN ('ch1', 'ch3')"),
])
def test_condition_text_for_values_without_quote(
    method: Callable[[list[str]], exp.Expression],
    values: list[str],
    expected: str,
) -> None:
    assert method(values).sql() == expected
