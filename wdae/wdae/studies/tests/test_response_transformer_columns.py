# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

import pytest
from gpf_instance.gpf_instance import WGPFInstance

from dae.configuration.gpf_config_parser import FrozenBox
from dae.person_sets import PersonSetCollection
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from studies.response_transformer import ResponseTransformer


def test_special_attrs_formatting(
    fixtures_wgpf_instance: WGPFInstance,
) -> None:
    genotype_data = fixtures_wgpf_instance.make_wdae_wrapper("f1_study")
    assert genotype_data is not None

    download_sources = genotype_data.get_columns_as_sources(
        genotype_data.config, genotype_data.download_columns,  # type: ignore
    )
    vs = genotype_data.query_variants_wdae({}, download_sources)
    vs = list(vs)
    row = vs[0]
    assert row == [
        ["f1"],
        ["f1_study"],
        ["1:878152"],
        ["sub(C->T,A)"],
        ["1"],
        ["878152"],
        ["C"],
        ["T", "A"],
        ["2111/0110/0001"],
        ["mom1;dad1;ch1;ch2"],
        ["mom:F:unaffected;dad:M:unaffected;prb:F:affected;sib:M:unaffected"],
        ["dad1;ch1", "ch2"],
        ["dad:M:unaffected;prb:F:affected", "sib:M:unaffected"],
        ["mendelian", "denovo"],
        "phenotype 1:unaffected:phenotype 1:unaffected",
        "unaffected:phenotype 1,unaffected",
        "test_phenotype",
    ]


@pytest.fixture()
def v_vcf(variants_impl: Any) -> FamilyVariant:
    vvars = variants_impl("variants_vcf")("backends/a")
    vs = list(vvars.query_variants(regions=[Region("1", 11548, 11548)]))
    assert len(vs) == 1

    v = vs[0]
    return cast(FamilyVariant, v)


@pytest.fixture()
def phenotype_person_sets(variants_impl: Any) -> PersonSetCollection:
    vvars = variants_impl("variants_vcf")("backends/a")
    families = vvars.families
    person_sets_config = FrozenBox({
        "id": "phenotype",
        "sources": [
            {
                "from": "pedigree",
                "source": "status",
            }],
        "default": {
            "id": "unknown",
            "name": "Unknown",
            "color": "#aaaaaa",
        },
        "domain": [
            {
                "id": "autism",
                "name": "Autism",
                "values": ["affected"],
                "color": "#ff0000",
            },
            {
                "id": "unaffected",
                "name": "Unaffected",
                "values": ["unaffected"],
                "color": "#0000ff",
            },
        ],
    })
    person_sets = PersonSetCollection.from_families(
        person_sets_config, families)
    assert person_sets is not None
    return person_sets


@pytest.mark.parametrize(
    "column,expected",
    [
        ("family", ["f"]),
        ("location", ["1:11548", "1:11548"]),
        ("variant", ["comp(T->AA,CA)"]),
        ("position", [11548, 11548]),
        ("reference", ["T", "T"]),
        ("alternative", ["AA", "CA"]),
        ("family_person_attributes", [
            "paternal_grandfather:M:unaffected;"
            "paternal_grandmother:F:unaffected;"
            "mom:F:unaffected;"
            "dad:M:unaffected;"
            "prb:F:affected;"
            "sib:F:unaffected;"
            "sib:F:unaffected"]),
        ("family_person_ids", ["gpa;gma;mom;dad;ch1;ch2;ch3"]),
        ("carrier_person_ids", ["gpa;gma;mom;dad;ch1;ch2;ch3", "mom"]),
        ("carrier_person_attributes", [
            "paternal_grandfather:M:unaffected;"
            "paternal_grandmother:F:unaffected;"
            "mom:F:unaffected;"
            "dad:M:unaffected;"
            "prb:F:affected;"
            "sib:F:unaffected;"
            "sib:F:unaffected",
            "mom:F:unaffected"]),
        ("genotype", ["1/1;1/1;1/2;1/1;1/1;1/1;1/1"]),
        ("best_st", ["0000000/2212222/0010000"]),
        ("inheritance_type", ["mendelian", "mendelian"]),
        ("is_denovo", [False, False]),
    ],
)
def test_special_attr_columns(
    v_vcf: FamilyVariant, column: str, expected: Any,
) -> None:

    transformer = ResponseTransformer.SPECIAL_ATTRS[column]

    result = transformer(v_vcf)
    assert result == expected


def test_reference_column(v_vcf: FamilyVariant) -> None:

    transformer = ResponseTransformer.SPECIAL_ATTRS["reference"]
    expected = ["T", "T"]

    result = transformer(v_vcf)
    assert result == expected


@pytest.mark.parametrize(
    "column,expected",
    [
        ("family_phenotypes", [
            "Unaffected:Unaffected:Unaffected:Unaffected:"
            "Autism:Unaffected:Unaffected"]),
        ("carrier_phenotypes", [
            "Unaffected:Unaffected:Unaffected:Unaffected:Autism:"
            "Unaffected:Unaffected",
            "Unaffected"]),
    ],
)
def test_phenotype_attr_columns(
    v_vcf: FamilyVariant,
    phenotype_person_sets: PersonSetCollection,
    column: str, expected: Any,
) -> None:

    print(phenotype_person_sets)

    transformer = ResponseTransformer.PHENOTYPE_ATTRS[column]

    result = transformer(v_vcf, phenotype_person_sets)
    assert result == expected
