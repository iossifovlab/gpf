import pytest


@pytest.mark.parametrize(
    "wrapper_type",
    ["local", "remote"]
)
def test_query_all_variants(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    variants = list(study_wrapper.get_variants_wdae_preview({}))

    assert len(variants) == 5645


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
        ("denovo", 5645),
        ("omission", 0),
        ("unknown", 5645),  # matches all variants
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
    variants = list(study_wrapper.get_variants_wdae_preview(query))

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    ["local", "remote"]
)
def test_query_limit_variants(iossifov_2014_wrappers, wrapper_type):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    variants = list(study_wrapper.get_variants_wdae_preview(
        {}, max_variants_count=1)
    )
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
        (["11542"], 3),
        (["11547"], 2),
        (["11542", "11547"], 5),
        ([], 0),
        (None, 5645)
    ],
)
def test_query_family_variants(
        iossifov_2014_wrappers, wrapper_type, family_ids, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "family_ids": family_ids
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (["M"], 3915),
        (["F"], 1751),
    ],
)
def test_query_sexes_variants(
        iossifov_2014_wrappers, wrapper_type, sexes, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "sexes": sexes
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (["ins"], 143),
        (["sub"], 5102),
        (["del"], 400),
    ],
)
def test_query_variant_type_variants(
        iossifov_2014_wrappers, wrapper_type, variant_type, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "variant_type": variant_type
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (["Intergenic"], 66),
        (["Missense"], 2808),
        (["Missense", "Intergenic"], 2874),
        (["CNV"], 0),
    ],
)
def test_query_effect_types_variants(
        iossifov_2014_wrappers, wrapper_type, effect_types, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "effect_types": effect_types
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (["1:0-100000000"], 232),
        (["2:0-100000000"], 169),
        (["1:11539-11539"], 0)
    ],
)
def test_query_regions_variants(
        iossifov_2014_wrappers, wrapper_type, regions, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "regions": regions
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (["proband only"], 3358),
        (["sibling only"], 2244),
        (["proband and sibling"], 43),
        (["neither"], 0),
        (["proband and sibling", "proband only"], 3401),
        (["proband only", "neither"], 3358),
        (
            ["proband only", "sibling only", "proband and sibling", "neither"],
            5645
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
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        ({"presentInParent": ["neither"]}, 5645),
        ({"presentInParent": ["mother and father", "mother only"]}, 0),
        ({"presentInParent": ["mother only", "neither"]}, 5645),
        ({"presentInParent": [
            "mother only",
            "father only",
            "mother and father",
            "neither",
        ]}, 5645),
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
    variants = list(study_wrapper.get_variants_wdae_preview(query))

    assert len(variants) == count


@pytest.mark.parametrize(
    "wrapper_type",
    [
        "local",
        "remote"
    ]
)
@pytest.mark.parametrize(
    "roles,count",
    [
        ({"prb": ["Proband"]}, 3401),
        ({"prb": ["Sibling"]}, 2287),
        ({"prb": ["Proband", "Sibling"]}, 5645),
    ],
)
def test_query_present_in_role(
        iossifov_2014_wrappers, wrapper_type, roles, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "presentInRole": roles
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (None, 5645),
        (25, 0),
        (50, 0),
        (100, 0)
    ],
)
def test_query_min_alt_frequency(
        iossifov_2014_wrappers, wrapper_type, option, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "minAltFrequencyPercent": option
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
        (None, 5645),
        (25, 0),
        (50, 0),
        (100, 0)
    ],
)
def test_query_max_alt_frequency(
        iossifov_2014_wrappers, wrapper_type, option, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "maxAltFrequencyPercent": option
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

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
            {"weight": "LGD_rank", "rangeStart": None, "rangeEnd": None},
            5328
        ),
        (
            {"weight": "LGD_rank", "rangeStart": 10.5, "rangeEnd": None},
            5301
        ),
        (
            {"weight": "LGD_rank", "rangeStart": None, "rangeEnd": 20000.0},
            5328
        ),
        (
            {"weight": "LGD_rank", "rangeStart": 2000.0, "rangeEnd": 4000.0},
            663
        ),
        (
            {"weight": "LGD_rank", "rangeStart": 9000.0, "rangeEnd": 11000.0},
            431
        ),
        (
            {"weight": "LGD_rank", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            369
        ),
        (
            {"weight": "ala bala", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            5645
        ),
    ],
)
def test_query_gene_weights(
        iossifov_2014_wrappers, wrapper_type, option, count):
    study_wrapper = iossifov_2014_wrappers[wrapper_type]
    query = {
        "geneWeights": option
    }
    variants = list(study_wrapper.get_variants_wdae_preview(query))

    assert len(variants) == count


def test_special_attrs_formatting(fixtures_wgpf_instance):
    genotype_data = fixtures_wgpf_instance.make_wdae_wrapper("f1_study")
    vs = genotype_data.get_variant_web_rows(
        {}, genotype_data.download_descs
    )
    row = list(vs)[0]
    assert row == [
        "f1",
        "f1_study",
        '1:878152',
        'sub(C->T,A)',
        '1',
        '878152',
        'C',
        'T,A',
        '2111/0110/0001',
        'mom1,dad1,ch1,ch2',
        'mom:F:unaffected,dad:M:unaffected,prb:F:affected,sib:M:unaffected',
        "['dad1', 'ch1'],['ch2']",
        "['dad:M:unaffected', 'prb:F:affected'],['sib:M:unaffected']",
        '[unknown, unknown, mendelian, missing],[unknown, unknown, missing, denovo]',
        'phenotype1:unaffected:phenotype1:unaffected',
        ['unaffected:phenotype1', 'unaffected'],
        "test_phenotype"
    ]
