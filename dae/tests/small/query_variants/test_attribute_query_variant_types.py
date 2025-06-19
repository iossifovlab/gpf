# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
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
        ("del or tandem_repeat", Allele.Type.tandem_repeat_ins, True),
        ("del and tandem_repeat", Allele.Type.tandem_repeat_ins, False),
        ("ins and tandem_repeat", Allele.Type.tandem_repeat_ins, True),
        ("cnv+ or cnv-", Allele.Type.large_duplication, True),
        ("cnv+ or cnv-", Allele.Type.large_deletion, True),
        ("cnv+ or cnv-", Allele.Type.substitution, False),
    ],
)
def test_simple_variant_types_parser(query, variant, expected):
    matcher = transform_attribute_query_to_function(
        Allele.Type, query, aliases=Allele.TYPE_DISPLAY_NAME,
    )
    assert matcher(variant.value) == expected


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
