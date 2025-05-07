# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
)
from dae.query_variants.attributes_query import (
    QueryTreeToBitwiseLambdaTransformer,
    QueryTreeToSQLBitwiseTransformer,
    variant_type_query,
)
from dae.variants.core import Allele


@pytest.mark.parametrize(
    "query,variant,expected",
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
def test_simple_variant_types_parser(query, variant, expected):
    parsed = variant_type_query.transform_query_string_to_tree(query)
    print(parsed)

    transformer = QueryTreeToSQLBitwiseTransformer("variant_type")
    matcher = transformer.transform(parsed)
    print(matcher)

    transformer = QueryTreeToBitwiseLambdaTransformer()
    matcher = transformer.transform(parsed)
    print(matcher)

    result = matcher([variant])
    print(result)

    assert result == expected


@pytest.mark.parametrize(
    "query,variant,expected",
    [
        (
            "substitution",
            Allele.Type.substitution,
            True,
        ),
        (
            "small_insertion",
            Allele.Type.small_insertion,
            True,
        ),
        (
            "small_insertion",
            Allele.Type.small_deletion,
            False,
        ),
        (
            "small_insertion or small_deletion",
            Allele.Type.small_deletion,
            True,
        ),
        (
            "small_insertion",
            Allele.Type.tandem_repeat_ins,
            True,
        ),
        (
            "small_deletion",
            Allele.Type.tandem_repeat_ins,
            False,
        ),
        (
            "small_deletion or tandem_repeat",
            Allele.Type.tandem_repeat_ins,
            True,
        ),
        (
            "small_deletion and tandem_repeat",
            Allele.Type.tandem_repeat_ins,
            False,
        ),
        (
            "small_insertion and tandem_repeat",
            Allele.Type.tandem_repeat_ins,
            True,
        ),
    ],
)
def test_attributes_query_function_transform(query, variant, expected):
    func = transform_attribute_query_to_function(Allele.Type, query)

    assert func(variant.value) == expected
