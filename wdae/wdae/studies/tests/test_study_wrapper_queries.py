# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from studies.study_wrapper import StudyWrapper


def test_query_all_variants(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    variants = list(
        study_wrapper.query_variants_wdae(
            {}, [{"source": "location"}],
            t4c8_query_transformer,
            t4c8_response_transformer,
        ),
    )

    assert len(variants) == 12, variants


@pytest.mark.parametrize(
    "inheritance_type,count",
    [
        ("unknown", 12),  # matches all variants
        ("omission", 0),
        ("denovo", 3),
        ("mendelian", 7),
    ],
)
def test_study_2_query_inheritance_variants(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    inheritance_type: str, count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "inheritance": inheritance_type,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

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
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    max_variants_count: int | None,
    count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    variants = list(study_wrapper.query_variants_wdae(
        {}, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
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
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    family_ids: list[str] | None, count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "family_ids": family_ids,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

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
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    sexes: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "genders": sexes,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "variant_type,count",
    [
        (["ins"], 5),
        (["sub"], 11),
        (["del"], 0),
        (["ins", "sub"], 12),
    ],
)
def test_query_variant_type_variants(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    variant_type: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "variantTypes": variant_type,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

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
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    effect_types: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "effect_types": effect_types,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

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
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    regions: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "regions": regions,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "options,count",
    [
        (["proband only"], 4),
        (["sibling only"], 3),
        (["proband and sibling"], 5),
        (["neither"], 5),
        (["proband and sibling", "proband only"], 9),
        (["proband only", "neither"], 8),
        (["proband only", "sibling only", "proband and sibling", "neither"],
         12),
    ],
)
def test_query_present_in_child(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    options: list[str], count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "presentInChild": options,
        "presentInParent": {
            "presentInParent": [
                "mother only", "father only", "mother and father", "neither",
            ],
        },
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "options,count",
    [
        ({"presentInParent": ["mother only"]}, 5),
        ({"presentInParent": ["father only"]}, 4),
        ({"presentInParent": ["mother and father"]}, 5),
        ({"presentInParent": ["neither"]}, 3),
        ({"presentInParent": ["mother and father", "mother only"]}, 10),
        ({"presentInParent": ["mother only", "neither"]}, 8),
        ({"presentInParent": [
            "mother only",
            "father only",
            "mother and father",
            "neither",
        ]}, 12),
    ],
)
def test_query_present_in_parent(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    options: dict, count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "presentInParent": options,
        "presentInChild": [
            "proband only", "sibling only", "proband and sibling", "neither",
        ],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,count", [
        (["proband and sibling"], ["neither"], 1),
        (["proband only"], ["neither"], 2),
        (["sibling only"], ["neither"], 1),
        (["proband only", "sibling only"], ["neither"], 3),
        (["proband only", "sibling only", "proband and sibling"],
         ["neither"], 4),
        (["proband only", "sibling only", "proband and sibling"],
         ["father only"], 1),
    ],
)
def test_query_present_in_parent_and_present_in_child(
    t4c8_study_2_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    present_in_child: list[str],
    present_in_parent: list[str],
    count: int,
) -> None:
    study_wrapper = t4c8_study_2_wrapper
    query = {
        "presentInParent": {
            "presentInParent": present_in_parent,
        },
        "presentInChild": present_in_child,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "option,count",
    [
        (
            {"score": "t4c8_score", "rangeStart": None, "rangeEnd": None},
            7,
        ),
        (
            {"score": "t4c8_score", "rangeStart": 15.0, "rangeEnd": None},
            5,
        ),
        (
            {"score": "t4c8_score", "rangeStart": None, "rangeEnd": 15.0},
            2,
        ),
        (
            {"score": "t4c8_score", "rangeStart": None, "rangeEnd": 20.0},
            7,
        ),
        (
            {"score": "t4c8_score", "rangeStart": 1.0, "rangeEnd": 9.0},
            0,
        ),
    ],
)
def test_query_gene_scores(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    option: dict, count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "geneScores": option,
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


def test_query_person_filters(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
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
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))
    assert len(variants) == 12


def test_query_family_filters(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        # this selects families in which the sibling has sex "F";
        # i.e. [f1.3]
        "familyFilters": [
            {
                "source": "sex",
                "sourceType": "categorical",
                "selection": {"selection": ["F"]},
                "from": "pedigree",
                "role": ["sib"],
            },
        ],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == 6


@pytest.mark.parametrize(
    "query,count",
    [
        (
            {
                "studyFilters": ["t4c8_study_1"],
                "regions": ["chr1:1-60"],
            }, 4,
        ),
        (
            {
                "studyFilters": ["t4c8_study_1"],
            }, 12,
        ),
        (
            {
                "studyFilters": ["ala_bala_study"],
            }, 0,
        ),
    ],
)
def test_query_study_filters(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    query: dict, count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    variants = list(study_wrapper.query_variants_wdae(
        query,
        [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


@pytest.mark.parametrize(
    "float_format, float_val",
    [
        ("%.2f", "10.12"),
        ("%.4f", "10.1235"),
        ("%.6f", "10.123457"),
    ],
)
def test_query_gene_scores_formatting(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    float_format: str,
    float_val: str,
) -> None:
    study_wrapper = t4c8_study_1_wrapper

    columns = [{
        "name": "t4c8_score",
        "source": "t4c8_score",
        "format": float_format,
    }]
    query = {
        "genes": ["t4"],
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, columns,
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))
    v = variants[0]

    assert v[0] == [float_val]


def test_query_complex_query(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    study_wrapper = t4c8_study_1_wrapper

    query = {
        "variantTypes": ["sub", "ins", "del"],
        "effectTypes": [
            "frame-shift", "nonsense", "splice-site",
            "no-frame-shift-newStop", "missense", "synonymous",
        ],
        "genders": [
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
                "unaffected",
            ],
        },
        "genomicScores": [],
        "frequencyScores": [],
        "uniqueFamilyVariants": False,
        "studyFilters": ["t4c8_study_1"],
        "datasetId": "t4c8_study_1",
        "maxVariantsCount": 1001,
    }
    vs = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))
    assert len(vs) == 2


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,phenotypes,count", [
        (["proband and sibling"], ["neither"], ["autism", "unaffected"], 2),
        (["proband and sibling", "proband", "neither"],
         ["mother and father", "neither"],
         ["autism", "unaffected"], 6),
        (["proband and sibling", "proband", "neither"],
         ["mother and father", "neither"],
         ["autism"], 4),
        (["proband and sibling", "proband", "neither"],
         ["mother and father", "neither"],
         ["unaffected"], 6),
    ],
)
def test_query_present_in_parent_and_present_in_child_and_phenotypes(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    present_in_child: list[str],
    present_in_parent: list[str],
    phenotypes: list[str],
    count: int,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    query = {
        "presentInParent": {
            "presentInParent": present_in_parent,
        },
        "presentInChild": present_in_child,
        "personSetCollection": {
            "id": "phenotype",
            "checkedValues": phenotypes,
        },
    }
    variants = list(study_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))

    assert len(variants) == count


def test_query_inheritance_types(
    t4c8_study_1_wrapper: StudyWrapper,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
):
    query = {
        "inheritanceTypeFilter": [
            "denovo", "mendelian", "omission", "missing",
        ],
    }

    variants = list(t4c8_study_1_wrapper.query_variants_wdae(
        query, [{"source": "location"}],
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))
    assert len(variants) == 12
