# pylint: disable=C0114,C0116
import pytest

from gpf.query_variants.sql.schema2.sql_query_builder import SqlQueryBuilder

BAD_ATTR = "phylop IS NOT NULL OR 1 = 1"


def test_real_attr_refuses_attr_name_that_is_not_an_identifier() -> None:
    with pytest.raises(ValueError, match="attribute name"):
        SqlQueryBuilder.real_attr([(BAD_ATTR, (0.0, 1.0))])


def test_categorical_attr_refuses_attr_name_that_is_not_an_identifier(
) -> None:
    with pytest.raises(ValueError, match="attribute name"):
        SqlQueryBuilder.categorical_attr([(BAD_ATTR, [1, 2])])


BAD_BOUNDS = [
    ("0 OR 1 = 1", 1.0),
    (0.0, "1 OR 1 = 1"),
    (True, 1.0),
    (0.0, False),
]


@pytest.mark.parametrize("value_range", BAD_BOUNDS)
def test_real_attr_refuses_bound_that_is_not_a_number(
    value_range: tuple,
) -> None:
    with pytest.raises(ValueError, match="bound"):
        SqlQueryBuilder.real_attr([("phylop", value_range)])


@pytest.mark.parametrize("value_range", BAD_BOUNDS)
def test_frequency_refuses_bound_that_is_not_a_number(
    value_range: tuple,
) -> None:
    with pytest.raises(ValueError, match="bound"):
        SqlQueryBuilder.frequency([("af_allele_freq", value_range)])


@pytest.mark.parametrize("value_range,expected", [
    ((0, 5), "sa.phylop >= 0 AND sa.phylop <= 5"),
    ((-1.5, None), "sa.phylop >= -1.5"),
    ((None, 2), "sa.phylop <= 2"),
    ((None, None), "NOT sa.phylop IS NULL"),
])
def test_real_attr_sql_text_for_number_and_none_bounds(
    value_range: tuple[float | None, float | None],
    expected: str,
) -> None:
    cond = SqlQueryBuilder.real_attr([("phylop", value_range)])

    assert cond.sql() == expected
