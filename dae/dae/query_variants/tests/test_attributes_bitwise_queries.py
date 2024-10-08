# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attributes_query import (
    PARSER,
    BitwiseTreeTransformer,
    QueryTreeToSQLBitwiseTransformer,
    inheritance_converter,
    inheritance_query,
)


@pytest.mark.parametrize(
    "query,expected",
    [
        ("mendelian", "BITAND(col, 2) != 0"),
        ("not mendelian", "(NOT (BITAND(col, 2) != 0))"),
        (
            "mendelian or denovo",
            "(BITAND(col, 2) != 0) OR (BITAND(col, 4) != 0)",
        ),
    ],
)
def test_bitwise_query(query, expected):
    parsed = inheritance_query.transform_query_string_to_tree(query)
    transformer = QueryTreeToSQLBitwiseTransformer("col")
    result = transformer.transform(parsed)
    print(result)
    assert expected == result


@pytest.mark.xfail(reason="FIXME: can't handle single 'mendelian' token")
@pytest.mark.parametrize(
    "query",
    [
        "not (mendelian or denovo)",
        "mendelian",
        "not mendelian",
        "mendelian or denovo",
        "mendelian or not denovo",
        "not (mendelian or denovo)",
        "not (mendelian and denovo)",
        "not (mendelian or not denovo)",
        "not (mendelian and not denovo)",
    ],
)
def test_experiments_with_bitwise_grammar(query):
    tree = PARSER.parse(query)
    print()
    print(tree.pretty())
    print()

    transformer = BitwiseTreeTransformer(inheritance_converter)
    res = transformer.transform(tree)
    print(res)
