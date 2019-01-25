from __future__ import unicode_literals

import pytest


def test_query_all_variants(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.query_variants())

    assert len(variants) == 14


@pytest.mark.parametrize("type,count", [
    ("denovo", 2),
    ("omission", 4),
    ("unknown", 14),  # matches all variants
    ("mendelian", 3),
    ("reference", 0)  # not returned unless return_reference is set to true
])
def test_query_inheritance_variants(type, count, inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.query_variants(inheritance=type))

    assert len(variants) == count


@pytest.mark.parametrize("families,count", [
    (["f1"], 1),
    (["f2"], 1),
    (["f1", "f2"], 2),
    ([], 0),
    # (None, 28)
])
def test_query_family_variants(families, count, quads_two_families_wrapper):
    variants = list(
        quads_two_families_wrapper.query_variants(family_ids=families))

    assert len(variants) == count


@pytest.mark.parametrize("sexes,count", [
    ("M", 2),
    ("F", 1),
])
def test_query_sexes_variants(sexes, count, quads_f1_wrapper):
    variants = list(quads_f1_wrapper.query_variants(sexes=sexes))

    assert len(variants) == count
