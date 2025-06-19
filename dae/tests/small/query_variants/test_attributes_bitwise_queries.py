# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_sql_expression_schema1,
)
from dae.variants.attributes import Inheritance
from sqlglot import column, parse_one


@pytest.mark.parametrize(
    "query,expected",
    [
        ("mendelian", "BITAND(col, 2) <> 0"),
        ("not mendelian", "NOT BITAND(col, 2) != 0"),
        (
            "mendelian or denovo",
            "BITAND(col, 2) != 0 OR BITAND(col, 4) != 0",
        ),
    ],
)
def test_bitwise_query(query, expected):
    query_glot = transform_attribute_query_to_sql_expression_schema1(
        Inheritance, query, column("col"),
    )
    expected_glot = parse_one(expected)
    assert query_glot == expected_glot
