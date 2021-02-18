import pytest
from dae.variants.attributes import VariantType
from dae.backends.attributes_query import QueryTreeToBitwiseLambdaTransformer, variant_type_query, \
    QueryTreeToSQLBitwiseTransformer


@pytest.mark.parametrize(
    "query,vt,expected",
    [
        ("ins", VariantType.insertion, True),
        ("ins", VariantType.deletion, False),
        ("ins or del", VariantType.deletion, True),
        ("ins", VariantType.tandem_repeat_ins, True),
        ("del", VariantType.tandem_repeat_ins, False),
        ("del or TR", VariantType.tandem_repeat_ins, True),
        ("del and TR", VariantType.tandem_repeat_ins, False),
        ("ins and TR", VariantType.tandem_repeat_ins, True),
    ],
)
def test_simple_variant_types_parser(query, vt, expected):
    parsed = variant_type_query.transform_query_string_to_tree(query)
    print(parsed)

    transformer = QueryTreeToSQLBitwiseTransformer("variant_type")
    matcher = transformer.transform(parsed)
    print(matcher)

    transformer = QueryTreeToBitwiseLambdaTransformer()
    matcher = transformer.transform(parsed)
    print(matcher)

    result = matcher([vt])
    print(result)

    assert result == expected
