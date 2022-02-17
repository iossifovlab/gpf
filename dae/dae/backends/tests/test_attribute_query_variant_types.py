import pytest
from dae.variants.core import Allele
from dae.backends.attributes_query import \
    QueryTreeToBitwiseLambdaTransformer, \
    variant_type_query, \
    QueryTreeToSQLBitwiseTransformer


@pytest.mark.parametrize(
    "query,vt,expected",
    [
        ("sub", Allele.Type.substitution, True),
        ("ins", Allele.Type.small_insertion, True),
        ("ins", Allele.Type.small_deletion, False),
        ("ins or del", Allele.Type.small_deletion, True),
        ("ins", Allele.Type.tandem_repeat_ins, True),
        ("del", Allele.Type.tandem_repeat_ins, False),
        ("del or TR", Allele.Type.tandem_repeat_ins, True),
        ("del and TR", Allele.Type.tandem_repeat_ins, False),
        ("ins and TR", Allele.Type.tandem_repeat_ins, True),
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
