from __future__ import unicode_literals

import pytest

pytestmark = pytest.mark.usefixtures("pheno_conf_path")


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


def test_query_limit_variants(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.query_variants(limit=1))

    assert len(variants) == 1


@pytest.mark.parametrize("families,count", [
    (["f1"], 1),
    (["f2"], 1),
    (["f1", "f2"], 2),
    ([], 0),
    # FIXME: (None, 28)
])
def test_query_family_variants(families, count, quads_two_families_wrapper):
    variants = list(
        quads_two_families_wrapper.query_variants(family_ids=families))

    assert len(variants) == count


@pytest.mark.parametrize("sexes,count", [
    (["M"], 2),
    (["F"], 1),
])
def test_query_sexes_variants(sexes, count, quads_f1_wrapper):
    variants = list(quads_f1_wrapper.query_variants(sexes=sexes))

    assert len(variants) == count


@pytest.mark.parametrize(
    "variant_type,count", [
        (["ins"], 1),
        (["sub"], 1),
        (["del"], 1)],
    ids=repr)
def test_query_variant_type_variants(
        variant_type, count, quads_variant_types_wrapper):
    variants = list(quads_variant_types_wrapper.query_variants(
        variant_type=variant_type))

    assert len(variants) == count


@pytest.mark.parametrize("effect_types,count", [
    (["Intergenic"], 2),
    (["CNV"], 0)
])
def test_query_effect_types_variants(effect_types, count, quads_f1_wrapper):
    variants = list(quads_f1_wrapper.query_variants(effect_types=effect_types))

    assert len(variants) == count


@pytest.mark.parametrize("regions,count", [
    (["1:0-100000000"], 1),
    (["2:0-100000000"], 1),
    (["1:11539-11539"], 1),
])
def test_query_regions_variants(regions, count, quads_f1_wrapper):
    variants = list(quads_f1_wrapper.query_variants(regions=regions))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (["affected only"], 1),
        (["unaffected only"], 1),
        (["affected and unaffected"], 1),
        (["neither"], 1),
        (["affected and unaffected", "affected only"], 2),
        (["affected only", "neither"], 2),
        ([
             "affected only", "unaffected only", "affected and unaffected",
             "neither"
         ], 4),
    ],
    ids=repr
)
def test_query_present_in_child(option, count, quads_in_child_wrapper):
    variants = list(quads_in_child_wrapper.query_variants(
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
        option, raw_query, quads_f1_wrapper):
    vs = quads_f1_wrapper.study \
        .query_variants(roles=raw_query)
    vs = list(vs)

    variants = list(quads_f1_wrapper.query_variants(presentInChild=option))
    assert len(vs) == len(variants)


def test_query_present_in_child_and_roles(quads_f1_wrapper):
    variants = list(quads_f1_wrapper.query_variants(
        presentInChild=["affected only"], roles="dad"))

    assert len(variants) == 1


@pytest.mark.parametrize(
    "option,count",
    [
        (["mother only"], 1),
        (["father only"], 1),
        (["mother and father"], 1),
        (["neither"], 1),
        (["mother and father", "mother only"], 2),
        (["mother only", "neither"], 2),
        ([
             "mother only", "father only", "mother and father",
             "neither"
         ], 4),
    ],
    ids=repr
)
def test_query_present_in_parent(option, count, quads_in_parent_wrapper):
    variants = list(quads_in_parent_wrapper.query_variants(
        presentInParent=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (None, 4),
        (25, 4),
        (50, 0),
        (100, 0),
    ]
)
def test_query_min_alt_frequency(option, count, quads_in_child_wrapper):
    variants = list(quads_in_child_wrapper.query_variants(
        minAltFrequencyPercent=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (None, 4),
        (0, 0),
        (12.5, 0),
        (25, 4),
        (100, 4),
    ]
)
def test_query_max_alt_frequency(option, count, quads_in_child_wrapper):
    variants = list(quads_in_child_wrapper.query_variants(
        maxAltFrequencyPercent=option))

    assert len(variants) == count


# FIXME: this is questionable for reference variants
@pytest.mark.parametrize(
    "minFreq,maxFreq,count",
    [
        (None, None, 4),
        (0, 0, 0),
        (0, 12.5, 0),
        (12.6, 25, 4),
        (25.1, 100, 0),
        (100, 100, 0),
    ]
)
def test_query_min_max_alt_frequency(
        minFreq, maxFreq, count, quads_in_child_wrapper):
    variants = list(quads_in_child_wrapper.query_variants(
        minAltFrequencyPercent=minFreq,
        maxAltFrequencyPercent=maxFreq))

    assert len(variants) == count


def test_query_with_matching_study_filter(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.
                    query_variants(studyFilters=[{'studyName': 'TRIO'}]))

    assert len(variants) == 14


def test_query_with_mismatching_study_filter(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.
                    query_variants(studyFilters=[{'studyName': 'QUADS_F1'}]))

    assert len(variants) == 0


def test_query_with_multiple_study_filters(inheritance_trio_wrapper):
    variants = list(inheritance_trio_wrapper.
                    query_variants(studyFilters=[{'studyName': 'QUADS_F1'},
                                                 {'studyName': 'TRIO'}]))
    assert len(variants) == 14

    variants = list(inheritance_trio_wrapper.
                    query_variants(studyFilters=[{'studyName': 'QUADS_F1'},
                                                 {'studyName': 'TEST_NAME'}]))
    assert len(variants) == 0
