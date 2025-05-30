# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
    update_attribute_query_with_compounds,
)
from dae.utils.variant_utils import BitmaskEnumTranslator
from dae.variants.attributes import Role, Zygosity

translator = BitmaskEnumTranslator(
    main_enum_type=Zygosity, partition_by_enum_type=Role,
)


@pytest.mark.parametrize(
    "query, role, zygosity, expected",
    [
        ("prb~heterozygous", Role.prb, Zygosity.heterozygous, True),
        ("prb~heterozygous", Role.prb, Zygosity.homozygous, False),
        ("prb~heterozygous", Role.sib, Zygosity.heterozygous, False),
        ("prb~heterozygous", Role.sib, Zygosity.homozygous, False),
        ("prb~heterozygous or sib", Role.sib, Zygosity.homozygous, True),
        ("prb~heterozygous and sib", Role.sib, Zygosity.homozygous, False),
    ],
)
def test_compound_zygosity(query, role, zygosity, expected):
    matcher = transform_attribute_query_to_function(
        Role, query, complementary_type=Zygosity,
    )

    bitmask = translator.apply_mask(0, zygosity.value, role)
    assert matcher(role.value, bitmask) == expected


@pytest.mark.parametrize(
    "query, zygosity_str, expected",
    [
        ("prb", "homozygous", "prb~homozygous"),
        ("prb or sib", "homozygous", "prb~homozygous or sib~homozygous"),
        ("prb and sib", "homozygous", "prb~homozygous and sib~homozygous"),
        ("(prb and sib)", "homozygous", "(prb~homozygous and sib~homozygous)"),
        ("not prb", "homozygous", "not prb~homozygous"),
        (
            "any([prb, sib])", "homozygous",
            "any([prb~homozygous, sib~homozygous])",
        ),
        (
            "all([prb, sib])", "homozygous",
            "all([prb~homozygous, sib~homozygous])",
        ),
        (
            "all([prb, sib]) or (dad and not prb)", "homozygous",
            "all([prb~homozygous, sib~homozygous]) or "
            "(dad~homozygous and not prb~homozygous)",
        ),
    ],
)
def test_compound_addition_to_query(query, zygosity_str, expected):
    assert update_attribute_query_with_compounds(
        query, zygosity_str) == expected
