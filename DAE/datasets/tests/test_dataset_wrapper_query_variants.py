import pytest


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


@pytest.mark.parametrize("sex,count", [
    ("M", 10),
    ("F", 12),
])
def test_query_sexes_variants(sex, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(sexes=sex))

    assert len(variants) == count


@pytest.mark.parametrize("variant_type,count", [
    ("ins", 2),
    ("sub", 22),
    ("del", 2),
])
def test_query_variant_type_variants(variant_type, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(variant_type=variant_type))

    assert len(variants) == count


@pytest.mark.parametrize("effect_types,count", [
    (["intergenic"], 16),
])
def test_query_effect_types_variants(effect_types, count, quads2_wrapper):
    variants = list(quads2_wrapper.get_variants(effect_types=effect_types))

    assert len(variants) == count


# @pytest.mark.parametrize("regions,count", [
#     (["1:0-100000000"], 16),
#     (["2:0-100000000"], 16),
# ])
# def test_query_regions_variants(regions, count, quads2_wrapper):
#     variants = list(quads2_wrapper.get_variants(regions=regions))
#
#     assert len(variants) == count
