# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest
from dae.person_sets import PersonSetCollection
from dae.studies.study import GenotypeData
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant

from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from studies.study_wrapper import WDAEStudy


def test_special_attrs_formatting(
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    study_wrapper = t4c8_study_1_wrapper
    assert study_wrapper is not None

    download_sources = study_wrapper.get_columns_as_sources(
        study_wrapper.config, study_wrapper.download_columns,
    )
    vs = list(study_wrapper.query_variants_wdae(
        {}, download_sources,
        t4c8_query_transformer,
        t4c8_response_transformer,
    ))
    row = vs[0]
    assert row is not None
    assert row == [
        ["f1.1"],
        ["t4c8_study_1"],
        "autism",
        ["chr1:4"],
        ["sub(T->G)"],
        ["chr1"],
        ["4"],
        ["T"],
        ["G"],
        ["mom1;dad1;p1;s1"],
        ["mom:F:unaffected;dad:M:unaffected;prb:F:affected;sib:M:unaffected"],
        ["1122/1100"],
        ["0/1;0/1;0/0;0/0"],
        ["mom1;dad1"],
        ["mom:F:unaffected;dad:M:unaffected"],
        ["mendelian"],
        "unaffected:unaffected:autism:unaffected",
        "unaffected:unaffected",
        ["4"],  # par_called
        ["37.5"],  # allele_freq
        ["intergenic"],
        ["intergenic"],
        ["intergenic:intergenic"],
        ["intergenic:intergenic:intergenic:intergenic"],
        ["-"],
        ["166.340"],  # f1.1 p1 age
        ["104.912"],  # f1.1 p1 IQ
    ]


@pytest.fixture(scope="module")
def fv1(t4c8_study_1: GenotypeData) -> FamilyVariant:
    vs = list(t4c8_study_1.query_variants(
        regions=[Region("chr1", 90, 90)],
        family_ids=["f1.3"],
    ))

    assert len(vs) == 1
    return vs[0]


@pytest.fixture(scope="module")
def fv2(t4c8_study_1: GenotypeData) -> FamilyVariant:
    vs = list(t4c8_study_1.query_variants(
        regions=[Region("chr1", 122, 200)],
        family_ids=["f1.3"],
    ))

    assert len(vs) == 1
    return vs[0]


@pytest.fixture(scope="module")
def phenotype_person_sets(t4c8_study_1: GenotypeData) -> PersonSetCollection:
    return t4c8_study_1.person_set_collections["phenotype"]


@pytest.mark.parametrize(
    "column,expected",
    [
        ("family", ["f1.3"]),
        ("location", ["chr1:90", "chr1:91"]),
        ("variant", ["sub(G->C)", "ins(A)"]),
        ("position", [90, 90]),
        ("reference", ["G", "G"]),
        ("alternative", ["C", "GA"]),
        ("family_person_attributes", [
            "mom:F:unaffected;"
            "dad:M:unaffected;"
            "prb:M:affected;"
            "sib:F:unaffected"]),
        ("family_person_ids", ["mom3;dad3;p3;s3"]),
        ("carrier_person_ids", ["mom3;p3", "dad3;s3"]),
        ("carrier_person_attributes", [
            "mom:F:unaffected;prb:M:affected",
            "dad:M:unaffected;sib:F:unaffected"]),
        ("genotype", ["0/1;0/2;0/1;0/2"]),
        ("best_st", ["1111/1010/0101"]),
        ("inheritance_type", ["mendelian", "mendelian"]),
        ("is_denovo", [False, False]),
    ],
)
def test_special_attr_columns(
    fv1: FamilyVariant, column: str, expected: Any,
) -> None:

    transformer = ResponseTransformer.SPECIAL_ATTRS[column]

    result = transformer(fv1)
    assert result == expected


@pytest.mark.parametrize(
    "column,expected",
    [
        ("family_phenotypes", [
            "unaffected:unaffected:autism:unaffected"]),
        ("carrier_phenotypes", [
            "unaffected:autism",
            "unaffected:unaffected"]),
    ],
)
def test_phenotype_attr_columns(
    fv1: FamilyVariant,
    phenotype_person_sets: PersonSetCollection,
    column: str, expected: list[str],
) -> None:

    transformer = ResponseTransformer.PHENOTYPE_ATTRS[column]

    result = transformer(fv1, phenotype_person_sets)
    assert result == expected


def test_inheritance_type_column(fv2: FamilyVariant) -> None:
    transformer = ResponseTransformer.SPECIAL_ATTRS["inheritance_type"]
    result = transformer(fv2)
    print(result)
    assert result == ["denovo", "mendelian"]


def test_is_denovo(fv2: FamilyVariant) -> None:
    transformer = ResponseTransformer.SPECIAL_ATTRS["is_denovo"]
    result = transformer(fv2)
    print(result)
    assert result == [True, False]
