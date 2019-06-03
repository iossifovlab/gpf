import pytest
from ..attributes_query import \
    QueryTreeToSQLBitwiseTransformer, \
    inheritance_query


@pytest.mark.parametrize("query,expected", [
    ("mendelian", "(BITAND(col, 2) != 0)"),
    ("not mendelian", "(NOT ((BITAND(col, 2) != 0)))"),
    ("mendelian or denovo",
        "((BITAND(col, 2) != 0)) OR ((BITAND(col, 4) != 0))"),
])
def test_bitwise_query(query, expected):
    parsed = inheritance_query.transform_query_string_to_tree(query)
    transformer = QueryTreeToSQLBitwiseTransformer("col")
    result = transformer.transform(parsed)
    print(result)
    assert expected == result
