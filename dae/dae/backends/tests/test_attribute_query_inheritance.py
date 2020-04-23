import pytest
from dae.variants.attributes import Inheritance
from dae.backends.attributes_query_inheritance import inheritance_parser, \
    InheritanceTransformer
from dae.backends.attributes_query import inheritance_query


@pytest.mark.parametrize(
    "query",
    [
        "denovo",
        "not denovo",
        "all ( denovo, possible_denovo ) ",
        "any(denovo,possible_denovo)",
        "denovo or possible_denovo",
        "denovo and possible_denovo",
        "not denovo and not possible_denovo",
    ],
)
def test_simple_inheritance_parser(query):
    tree = inheritance_parser.parse(query)
    print(tree)

    print(dir(tree))

    transformer = InheritanceTransformer("col")
    res = transformer.transform(tree)
    print("RES:", res, type(res))

    t = inheritance_query.transform_query_string_to_tree(query)
    m = inheritance_query.transform_tree_to_matcher(t)

    print(
        m.match([Inheritance.denovo]),
        m.match([Inheritance.possible_denovo]))