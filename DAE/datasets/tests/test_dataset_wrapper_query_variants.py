import pytest

from variants.attributes import Role


def test_query_all_variants(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.get_variants())

    assert len(variants) == 15


@pytest.mark.parametrize("type,count", [
    ("denovo", 4),
    ("omission", 5),
    ("unknown", 1),
    ("mendelian", 4),
    ("reference", 1)
])
def test_query_inheritance_variants(type, count, inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.get_variants(inheritance=type))

    assert len(variants) == count


def test_query_limit_variants(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.get_variants(limit=1))

    assert len(variants) == 1


@pytest.mark.parametrize("families,count", [
    (["f1"], 14),
    (["f2"], 14),
    (["f1", "f2"], 28),
    ([], 0),
    # FIXME: (None, 28)
])
def test_query_family_variants(families, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(family_ids=families))

    assert len(variants) == count


@pytest.mark.parametrize("sexes,count", [
    (["M"], 15),
    (["F"], 15),
])
def test_query_sexes_variants(sexes, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(sexes=sexes))

    assert len(variants) == count


@pytest.mark.parametrize("variant_type,count", [
    (["ins"], 2),
    (["sub"], 12),
    (["del"], 2),
])
def test_query_variant_type_variants(variant_type, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(variant_type=variant_type))

    assert len(variants) == count


@pytest.mark.parametrize("effect_types,count", [
    (["Intergenic"], 18),
    (["CNV"], 0)
])
def test_query_effect_types_variants(effect_types, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(effect_types=effect_types))

    assert len(variants) == count


@pytest.mark.parametrize("regions,count", [
    (["1:0-100000000"], 22),
    (["2:0-100000000"], 6),
])
def test_query_regions_variants(regions, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(regions=regions))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (["affected only"], 8),
        (["unaffected only"], 1),
        (["affected and unaffected"], 1),
        (["neither"], 19),
        (["affected and unaffected", "affected only"], 9),
        (["affected only", "neither"], 27),
        ([
             "affected only", "unaffected only", "affected and unaffected",
             "neither"
         ], 28),
    ],
    ids=repr
)
def test_query_present_in_child(option, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        presentInChild=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,raw_query",
    [
        (["affected only"], "prb and not sib"),
        (["unaffected only"], "sib and not prb"),
        (["affected and unaffected"], "sib and prb"),
        (["neither"], "not sib and not prb"),
    ],
    ids=repr
)
def test_query_present_in_child_compared_to_raw(
        option, raw_query, quads2_wrapper):
    vs = quads2_wrapper._variants.query_variants(roles=raw_query)
    vs = list(vs)

    variants = list(quads2_wrapper.get_variants(presentInChild=option))
    assert len(vs) == len(variants)


def test_query_present_in_child_and_roles(quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        presentInChild=["affected only"], roles="dad"))

    assert len(variants) == 3


@pytest.mark.parametrize(
    "option,count",
    [
        (["mother only"], 4),
        (["father only"], 3),
        (["mother and father"], 8),
        (["neither"], 15),
        (["mother and father", "mother only"], 12),
        (["mother only", "neither"], 19),
        ([
             "mother only", "father only", "mother and father",
             "neither"
         ], 28),
    ],
    ids=repr
)
def test_query_present_in_parent(option, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        presentInParent=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (None, 18),
        (25, 11),
        (50, 4),
        (100, 4),
    ]
)
def test_quary_min_alt_frequency(option, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        minAltFrequencyPercent=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (None, 0),
        (0, 4),
        (12.5, 7),
        (25, 14),
        (100, 18),
    ]
)
def test_quary_max_alt_frequency(option, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        maxAltFrequencyPercent=option))

    assert len(variants) == count


# FIXME: this is questionable for reference variants
@pytest.mark.parametrize(
    "minFreq,maxFreq,count",
    [
        (None, None, 28),
        (0, 0, 4),
        (0, 12.5, 7),
        (12.6, 25, 7),
        (25.1, 100, 4),
        (100, 100, 4),
    ]
)
def test_quary_max_alt_frequency_2(minFreq, maxFreq, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(
        minAltFrequencyPercent=minFreq,
        maxAltFrequencyPercent=maxFreq))

    assert len(variants) == count
