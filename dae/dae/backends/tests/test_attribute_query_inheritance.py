import pytest
from dae.variants.attributes import Inheritance
from dae.backends.attributes_query_inheritance import inheritance_parser, \
    InheritanceTransformer
from dae.backends.attributes_query import inheritance_query


@pytest.mark.parametrize(
    "query,exp1,exp2,exp3",
    [
        ("denovo", True, False, True),
        ("not denovo", False, True, True),
        ("all (denovo, possible_denovo )", False, False, True),
        ("any(denovo,possible_denovo)", True, True, True),
        ("denovo or possible_denovo", True, True, True),
        ("denovo and possible_denovo", False, False, True),
        ("not denovo and not possible_denovo", False, False, False),
        # # "any(denovo,mendelian) and not possible_denovo"
    ],
)
def test_simple_inheritance_parser(query, exp1, exp2, exp3):
    tree = inheritance_parser.parse(query)
    print(tree)

    transformer = InheritanceTransformer("col")
    res = transformer.transform(tree)
    print("RES:", res, type(res))

    t = inheritance_query.transform_query_string_to_tree(query)
    m = inheritance_query.transform_tree_to_matcher(t)

    print(
        m.match([Inheritance.denovo]),
        m.match([Inheritance.possible_denovo]))

    assert m.match([Inheritance.denovo]) == exp1
    assert m.match([Inheritance.possible_denovo]) == exp2
