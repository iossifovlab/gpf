# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.variants.attributes import Inheritance
from dae.query_variants.attributes_query_inheritance import inheritance_parser, \
    InheritanceTransformer
from dae.query_variants.attributes_query import inheritance_query


@pytest.mark.parametrize(
    "query,exp1,exp2",
    [
        ("denovo", True, False),
        ("not denovo", False, True),
        ("all (denovo, possible_denovo )", False, False),
        ("any(denovo,possible_denovo)", True, True),
        ("denovo or possible_denovo", True, True),
        ("denovo and possible_denovo", False, False),
        ("not denovo and not possible_denovo", False, False),
        # # "any(denovo,mendelian) and not possible_denovo"
    ],
)
def test_simple_inheritance_parser(query, exp1, exp2):
    tree = inheritance_parser.parse(query)
    print(tree)

    transformer = InheritanceTransformer("col")
    res = transformer.transform(tree)
    print("RES:", res, type(res))

    tree = inheritance_query.transform_query_string_to_tree(query)
    matcher = inheritance_query.transform_tree_to_matcher(tree)

    print(
        matcher.match([Inheritance.denovo]),
        matcher.match([Inheritance.possible_denovo]))

    assert matcher.match([Inheritance.denovo]) == exp1
    assert matcher.match([Inheritance.possible_denovo]) == exp2
