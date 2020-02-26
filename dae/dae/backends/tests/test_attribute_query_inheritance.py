import pytest
from dae.backends.attributes_query_inheritance import inheritance_parser, \
    InheritanceTransformer


@pytest.mark.parametrize("query", [
    "denovo",
    "not denovo",
    "all ( denovo, possible_denovo ) ",
    "any(denovo,possible_denovo)",
    "denovo or possible_denovo",
    "denovo and possible_denovo",
    "not denovo and not possible_denovo",
])
def test_simple_inheritance_parser(query):
    tree = inheritance_parser.parse(query)
    print(tree)

    transformer = InheritanceTransformer("col")
    res = transformer.transform(tree)
    print("RES:", res, type(res))
