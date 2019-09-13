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
    (["M"], 3),
    (["F"], 2),
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
    (["Intergenic"], 3),
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
        (["proband only"], 1),
        (["sibling only"], 1),
        (["proband and sibling"], 1),
        (["neither"], 1),
        (["proband and sibling", "proband only"], 2),
        (["proband only", "neither"], 2),
        ([
             "proband only", "sibling only", "proband and sibling",
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
        (["proband only"], "prb and not sib"),
        (["sibling only"], "sib and not prb"),
        (["proband and sibling"], "sib and prb"),
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
        presentInChild=["proband only"], roles="dad"))

    assert len(variants) == 1


@pytest.mark.parametrize(
    "option,count",
    [
        ({'presentInParent': ["mother only"]}, 1),
        ({'presentInParent': ["father only"]}, 1),
        ({'presentInParent': ["mother and father"]}, 1),
        ({'presentInParent': ["neither"]}, 1),
        ({'presentInParent': ["mother and father", "mother only"]}, 2),
        ({'presentInParent': ["mother only", "neither"]}, 2),
        ({'presentInParent': [
             "mother only", "father only", "mother and father",
             "neither"
         ]}, 4),
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
        ({"prb": ["Proband"]}, 2),
        ({"prb": ["Sibling"]}, 2),
        ({"prb": ["Proband", "Sibling"]}, 3),
        ({"prb": ["neither"]}, 1),
        ({"prb": ["Proband", "neither"]}, 3),
        ({"prb": ["Proband", "Sibling", "neither"]}, 4),
    ],
    ids=repr
)
def test_query_present_in_role(option, count, quads_in_child_wrapper):
    variants = list(quads_in_child_wrapper.query_variants(
        presentInRole=option))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,raw_query",
    [
        ({"prb": ["Proband"]}, "prb"),
        ({"prb": ["Sibling"]}, "sib"),
        ({"prb": ["Proband", "Sibling"]}, "prb or sib"),
        ({"prb": ["neither"]}, "not prb and not sib"),
    ],
    ids=repr
)
def test_query_present_in_role_compared_to_raw(
        option, raw_query, quads_f1_wrapper):
    vs = quads_f1_wrapper.studies[0]\
        .query_variants(roles=raw_query)
    vs = list(vs)

    variants = list(quads_f1_wrapper.query_variants(
        presentInRole=option))
    assert len(vs) == len(variants)


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


@pytest.mark.parametrize("geneWeights,count", [
    ({'weight': 'LGD_rank', 'rangeStart': None, 'rangeEnd': None}, 5),
    ({'weight': 'LGD_rank', 'rangeStart': 10.5, 'rangeEnd': None}, 5),
    ({'weight': 'LGD_rank', 'rangeStart': None, 'rangeEnd': 20000.0}, 5),
    ({'weight': 'LGD_rank', 'rangeStart': 2000.0, 'rangeEnd': 4000.0}, 1),
    ({'weight': 'LGD_rank', 'rangeStart': 9000.0, 'rangeEnd': 11000.0}, 4),
    ({'weight': 'LGD_rank', 'rangeStart': 1000.0, 'rangeEnd': 2000.0}, 0),
    ({'weight': 'ala bala', 'rangeStart': 1000.0, 'rangeEnd': 2000.0}, 5),
])
def test_query_gene_weights(
        geneWeights, count, quads_f2_wrapper):
    variants = list(quads_f2_wrapper.query_variants(
        geneWeights=geneWeights))

    assert len(variants) == count

    all_variants = list(quads_f2_wrapper.query_variants())

    assert len(all_variants) == 5


@pytest.mark.parametrize("genomicScores,count", [
    ([{'metric': 'score1', 'rangeStart': None, 'rangeEnd': None}], 5),
    ([{'metric': 'score1', 'rangeStart': 10.5, 'rangeEnd': None}], 4),
    ([{'metric': 'score1', 'rangeStart': None, 'rangeEnd': 25.0}], 1),
    ([{'metric': 'score1', 'rangeStart': 2.0, 'rangeEnd': 7.0}], 1),
    ([{'metric': 'score1', 'rangeStart': 40.5, 'rangeEnd': 55.0}], 2),
    ([{'metric': 'score1', 'rangeStart': 42.0, 'rangeEnd': 43.0}], 0),
    ([{'metric': 'ala bala', 'rangeStart': 5.0, 'rangeEnd': 50.0}], 0),
    ([{'metric': 'score1', 'rangeStart': 2.0, 'rangeEnd': 7.0},
      {'metric': 'score2', 'rangeStart': 50.0, 'rangeEnd': 150.0}], 1),
    ([{'metric': 'score1', 'rangeStart': 2.0, 'rangeEnd': 7.0},
      {'metric': 'score2', 'rangeStart': 50.0, 'rangeEnd': 75.0}], 0),
])
def test_query_genomic_scores(genomicScores, count, quads_f2_wrapper):
    variants = list(quads_f2_wrapper.query_variants(
        genomicScores=genomicScores))

    assert len(variants) == count
