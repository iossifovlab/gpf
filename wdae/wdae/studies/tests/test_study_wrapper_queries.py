# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from studies.study_wrapper import StudyWrapperBase

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance",
    "dae_calc_gene_sets",
    # "agp_gpf_instance",
)


def test_query_all_variants(
    t4c8_study_2: StudyWrapperBase,
) -> None:
    study_wrapper = t4c8_study_2
    variants = list(study_wrapper.query_variants_wdae(
        {}, [{"source": "location"}]))

    assert len(variants) == 12, variants


@pytest.mark.parametrize(
    "inheritance_type,count",
    [
        ("unknown", 12),  # matches all variants
        ("omission", 0),
        ("denovo", 2),
        ("mendelian", 7),
    ],
)
def test_study_2_query_inheritance_variants(
    t4c8_study_2: StudyWrapperBase,
    inheritance_type: str, count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "inheritance": inheritance_type,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "max_variants_count,count",
    [
        (None, 12),  # matches all variants
        (1, 1),
        (2, 2),
        (50, 12),
    ],
)
def test_query_limit_variants(
    t4c8_study_2: StudyWrapperBase,
    max_variants_count: int | None,
    count: int,
) -> None:
    study_wrapper = t4c8_study_2
    variants = list(study_wrapper.query_variants_wdae(
        {}, [{"source": "location"}],
        max_variants_count=max_variants_count,
    ))
    assert len(variants) == count


@pytest.mark.parametrize(
    "family_ids,count",
    [
        (["f1.1"], 6),
        (["f1.3"], 6),
        (["f1.1", "f1.3"], 12),
        ([], 0),
        (None, 12),
    ],
)
def test_query_family_variants(
    t4c8_study_2: StudyWrapperBase,
    family_ids: list[str] | None, count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "family_ids": family_ids,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "sexes,count",
    [
        (["M"], 10),
        (["F"], 12),
        (["M", "F"], 12),
    ],
)
def test_query_sexes_variants(
    t4c8_study_2: StudyWrapperBase,
    sexes: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "gender": sexes,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "variant_type,count",
    [
        (["ins"], 5),
        (["sub"], 10),
        (["del"], 0),
        (["ins", "sub"], 12),
    ],
)
def test_query_variant_type_variants(
    t4c8_study_2: StudyWrapperBase,
    variant_type: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "variantTypes": variant_type,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "effect_types,count",
    [
        (["Intergenic"], 5),
        (["Missense"], 2),
        (["Missense", "Intergenic"], 7),
        (["CNV"], 0),
    ],
)
def test_query_effect_types_variants(
    t4c8_study_2: StudyWrapperBase,
    effect_types: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "effect_types": effect_types,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "regions,count",
    [
        (["chr1:1-60"], 4),
        (["chr1:1-99"], 6),
        (["chr1:100-150"], 6),
    ],
)
def test_query_regions_variants(
    t4c8_study_2: StudyWrapperBase,
    regions: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "regions": regions,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "options,count",
    [
        (["proband only"], 9),
        (["sibling only"], 0),
        (["proband and sibling"], 0),
        (["neither"], 7),
        (["proband and sibling", "proband only"], 9),
        (["proband only", "neither"], 12),
        (["proband only", "sibling only", "proband and sibling", "neither"],
         12),
    ],
)
def test_query_present_in_child(
    t4c8_study_2: StudyWrapperBase,
    options: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "presentInChild": options,
        "presentInParent": {
            "presentInParent": [
                "mother only", "father only", "mother and father", "neither",
            ],
        },
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "options,count",
    [
        ({"presentInParent": ["mother only"]}, 4),
        ({"presentInParent": ["father only"]}, 4),
        ({"presentInParent": ["mother and father"]}, 6),
        ({"presentInParent": ["neither"]}, 2),
        ({"presentInParent": ["mother and father", "mother only"]}, 10),
        ({"presentInParent": ["mother only", "neither"]}, 6),
        ({"presentInParent": [
            "mother only",
            "father only",
            "mother and father",
            "neither",
        ]}, 12),
    ],
)
def test_query_present_in_parent(
    t4c8_study_2: StudyWrapperBase,
    options: dict, count: int,
) -> None:
    study_wrapper = t4c8_study_2
    query = {
        "presentInParent": options,
        "presentInChild": [
            "proband only", "sibling only", "proband and sibling", "neither",
        ],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (
            {"score": "LGD_rank", "rangeStart": None, "rangeEnd": None},
            16,
        ),
        (
            {"score": "LGD_rank", "rangeStart": 10.5, "rangeEnd": None},
            16,
        ),
        (
            {"score": "LGD_rank", "rangeStart": None, "rangeEnd": 20000.0},
            16,
        ),
        (
            {"score": "LGD_rank", "rangeStart": 2000.0, "rangeEnd": 4000.0},
            0,
        ),
        (
            {"score": "LGD_rank", "rangeStart": 9000.0, "rangeEnd": 11000.0},
            2,
        ),
        (
            {"score": "LGD_rank", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            0,
        ),
        (
            {"score": "ala bala", "rangeStart": 1000.0, "rangeEnd": 2000.0},
            16,
        ),
    ],
)
def test_query_gene_scores(
    iossifov_2014_local: StudyWrapperBase,
    option: dict, count: int,
) -> None:
    study_wrapper = iossifov_2014_local
    query = {
        "geneScores": option,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == count


def test_query_person_filters(
    iossifov_2014_local: StudyWrapperBase,
) -> None:
    study_wrapper = iossifov_2014_local
    query = {
        "personFilters": [
            {
                "source": "phenotype",
                "sourceType": "categorical",
                "selection": {"selection": ["unaffected"]},
                "from": "pedigree",
            },
        ],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )
    assert len(variants) == 2


def test_query_family_filters(
    iossifov_2014_local: StudyWrapperBase,
) -> None:
    study_wrapper = iossifov_2014_local
    query = {
        "familyFilters": [
            {
                "source": "sex",
                "sourceType": "categorical",
                "selection": {"selection": ["M"]},
                "from": "pedigree",
                "role": ["prb"],
            },
        ],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )
    assert len(variants) == 15


def test_query_study_filters(
    iossifov_2014_local: StudyWrapperBase,
) -> None:
    study_wrapper = iossifov_2014_local
    query = {
        "studyFilters": ["iossifov_2014"],
        "regions": ["12"],
    }

    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )

    assert len(variants) == 2

    variants = list(study_wrapper.query_variants_wdae(
        {"studyFilters": ["iossifov_2014"]}, [{"source": "location"}]),
    )

    assert len(variants) == 16


def test_query_family_types(
    iossifov_2014_local: StudyWrapperBase,
) -> None:
    study_wrapper = iossifov_2014_local
    query = {
        "familyTypes": ["trio"],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]),
    )
    assert len(variants) == 1


@pytest.mark.parametrize(
    "float_format, float_val",
    [
        ("%.2f", "0.16"),
        ("%.4f", "0.1642"),
    ],
)
def test_query_gene_scores_formatting(
    iossifov_2014_local: StudyWrapperBase,
    float_format: str,
    float_val: str,
) -> None:
    study_wrapper = iossifov_2014_local

    columns = [{"name": "pLI", "source": "pLI", "format": float_format}]
    query = {
        "family_ids": ["13943"],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, columns),
    )
    v = variants[0]
    source_pli = {"name": "pLI", "source": "pLI"}
    source_pli.update({"format": float_format})
    assert source_pli in columns
    assert v[0] == [float_val]


def test_query_complex_query(
    iossifov_2014_local: StudyWrapperBase,
) -> None:
    study_wrapper = iossifov_2014_local

    query = {
        "variantTypes": ["sub", "ins", "del"],
        "effectTypes": [
            "frame-shift", "nonsense", "splice-site",
            "no-frame-shift-newStop",
        ],
        "gender": [
            "female", "male",
        ],
        "inheritanceTypeFilter": [],
        "presentInChild": [
            "proband only", "proband and sibling",
        ],
        "presentInParent": {
            "presentInParent": ["neither"],
        },
        "studyTypes": ["we", "wg", "tg"],
        "personSetCollection": {
            "id": "phenotype",
            "checkedValues": [
                "autism",
                "congenital_heart_disease",
                "developmental_disorder",
                "epilepsy",
                "intellectual_disability",
                "schizophrenia",
                "unaffected",
            ],
        },
        "familyTypes": [
            "trio", "quad", "multigenerational", "simplex",
            "multiplex", "other",
        ],
        "genomicScores": [],
        "frequencyScores": [],
        "uniqueFamilyVariants": False,
        "studyFilters": [],
        "datasetId": "sequencing_de_novo",
        "maxVariantsCount": 1001,
    }
    vs = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}]))
    assert len(vs) == 9
