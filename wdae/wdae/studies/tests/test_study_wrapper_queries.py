import pytest


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance",
    "dae_calc_gene_sets",
    "agp_gpf_instance",
)


@pytest.mark.parametrize(
    "wrapper_type",
    ["local", "remote"]
)
def test_query_all_variants(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    variants = list(study_wrapper.query_variants_wdae(
        {}, [{"source": "location"}]))

    assert len(variants) == 16, variants


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "inheritance_type,count",
    [
        ("denovo", 16),
        ("omission", 0),
        ("unknown", 16),  # matches all variants
        ("mendelian", 0),
        (
            "reference",
            0,
        ),  # not returned unless return_reference is set to true
    ],
)
def test_query_inheritance_variants(
        iossifov_2014_wrappers, wrapper_type, inheritance_type, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "inheritance": inheritance_type
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    ["local", "remote"]
)
def test_query_limit_variants(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    variants = list(study_wrapper.query_variants_wdae(
        {}, [{"source": "location"}], max_variants_count=1
    ))
    assert len(variants) == 1


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "family_ids,count",
    [
        (["12628"], 6),
        (["13590"], 1),
        (["12628", "13590"], 7),
        ([], 0),
        (None, 16)
    ],
)
def test_query_family_variants(
        iossifov_2014_wrappers, wrapper_type, family_ids, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "family_ids": family_ids
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "sexes,count",
    [
        (["M"], 13),
        (["F"], 3),
    ],
)
def test_query_sexes_variants(
        iossifov_2014_wrappers, wrapper_type, sexes, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "gender": sexes
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "variant_type,count",
    [
        (["ins"], 3),
        (["sub"], 4),
        (["del"], 9),
    ],
)
def test_query_variant_type_variants(
        iossifov_2014_wrappers, wrapper_type, variant_type, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "variantTypes": variant_type
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "effect_types,count",
    [
        (["Intergenic"], 0),
        (["Missense"], 2),
        (["Missense", "Intergenic"], 2),
        (["CNV"], 0),
    ],
)
def test_query_effect_types_variants(
        iossifov_2014_wrappers, wrapper_type, effect_types, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "effect_types": effect_types
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "regions,count",
    [
        (["3:0-100000000"], 2),
        (["2:0-100000000"], 2),
        (["1:11539-11539"], 0)
    ],
)
def test_query_regions_variants(
        iossifov_2014_wrappers, wrapper_type, regions, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "regions": regions
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "options,count",
    [
        (["proband only"], 14),
        (["sibling only"], 2),
        (["proband and sibling"], 0),
        (["neither"], 0),
        (["proband and sibling", "proband only"], 14),
        (["proband only", "neither"], 14),
        (
            ["proband only", "sibling only", "proband and sibling", "neither"],
            16
        )
    ],
)
def test_query_present_in_child(
        iossifov_2014_wrappers, wrapper_type, options, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "presentInChild": options,
        "presentInParent": {
            "presentInParent": [
                "mother only", "father only", "mother and father", "neither"
            ]
        }
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "options,count",
    [
        ({"presentInParent": ["mother only"]}, 0),
        ({"presentInParent": ["father only"]}, 0),
        ({"presentInParent": ["mother and father"]}, 0),
        ({"presentInParent": ["neither"]}, 16),
        ({"presentInParent": ["mother and father", "mother only"]}, 0),
        ({"presentInParent": ["mother only", "neither"]}, 16),
        ({"presentInParent": [
            "mother only",
            "father only",
            "mother and father",
            "neither",
        ]}, 16),
    ],
)
def test_query_present_in_parent(
        iossifov_2014_wrappers, wrapper_type, options, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "presentInParent": options,
        "presentInChild": [
            "proband only", "sibling only", "proband and sibling", "neither"
        ]
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "option,count",
    [
        (
            {"score": "LGD_rank", "rangeStart": None, "rangeEnd": None},
            16
        ),
        (
            {"score": "LGD_rank", "rangeStart": 10.5, "rangeEnd": None},
            16
        ),
        (
            {"score": "LGD_rank", "rangeStart": None, "rangeEnd": 20000.0},
            16
        ),
        (
            {"score": "LGD_rank", "rangeStart": 2000.0, "rangeEnd": 4000.0},
            0
        ),
        (
            {"score": "LGD_rank", "rangeStart": 9000.0, "rangeEnd": 11000.0},
            2
        ),
        (
            {"score": "LGD_rank", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            0
        ),
        (
            {"score": "ala bala", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            16
        ),
    ],
)
def test_query_gene_scores(
        iossifov_2014_wrappers, wrapper_type, option, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "geneScores": option
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
def test_query_person_filters(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "personFilters": [
            {
                "source": "phenotype",
                "sourceType": "categorical",
                "selection": {"selection": ["unaffected"]},
                "from": "pedigree",
            }
        ]
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )
    assert len(variants) == 2


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
def test_query_family_filters(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "familyFilters": [
            {
                "source": "sex",
                "sourceType": "categorical",
                "selection": {"selection": ["M"]},
                "from": "pedigree",
                "role": ["prb"],
            }
        ]
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )
    assert len(variants) == 15


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
def test_query_family_types(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "familyTypes": ["trio"]
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}])
    )
    assert len(variants) == 1
