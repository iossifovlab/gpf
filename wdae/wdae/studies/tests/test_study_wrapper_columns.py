import pytest

from dae.utils.regions import Region
from studies.study_wrapper import StudyWrapper


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
        'mom1;dad1;ch1;ch2',
        'mom:F:unaffected;dad:M:unaffected;prb:F:affected;sib:M:unaffected',
        "dad1;ch1,ch2",
        "dad:M:unaffected;prb:F:affected,sib:M:unaffected",
        '[unknown, unknown, mendelian, missing],'
        '[unknown, unknown, missing, denovo]',
        'phenotype1:unaffected:phenotype1:unaffected',
        ['unaffected:phenotype1', 'unaffected'],
        "test_phenotype"
    ]


@pytest.fixture
def v_impala(variants_impl):
    vvars = variants_impl("variants_impala")("backends/a")
    vs = list(vvars.query_variants(regions=[Region("1", 11548, 11548)]))
    assert len(vs) == 1

    v = vs[0]
    return v


@pytest.fixture
def v_vcf(variants_impl):
    vvars = variants_impl("variants_vcf")("backends/a")
    vs = list(vvars.query_variants(regions=[Region("1", 11548, 11548)]))
    assert len(vs) == 1

    v = vs[0]
    return v


@pytest.mark.parametrize(
    "column,expected",
    [
        ("family", ["f"]),
        ("location", ['1:11548', '1:11548']),
        ("variant", ['comp(T->AA,CA)']),
        ("position", [11548, 11548]),
        ("reference", ["T", "T"]),
        ("alternative", ['AA', 'CA']),
        ("family_structure", [
            'paternal_grandfather:M:unaffected;'
            'paternal_grandmother:F:unaffected;'
            'mom:F:unaffected;'
            'dad:M:unaffected;'
            'prb:F:affected;'
            'sib:F:unaffected;'
            'sib:F:unaffected']),
        ("family_person_ids", ['gpa;gma;mom;dad;ch1;ch2;ch3']),
        ("carrier_person_ids", ['gpa;gma;mom;dad;ch1;ch2;ch3', 'mom']),
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
        ("best_st", ["0000000/0000000/2212222/0010000/0000000"]),

    ]
)
def test_special_attr_columns(v_impala, v_vcf, column, expected):

    fn = StudyWrapper.SPECIAL_ATTRS_FORMAT[column]

    result = fn(v_impala)
    assert result == expected

    result = fn(v_vcf)
    assert result == expected


def test_reference_column(v_impala, v_vcf):

    fn = StudyWrapper.SPECIAL_ATTRS_FORMAT["reference"]
    expected = ["T", "T"]

    result = fn(v_impala)
    assert result == expected

    result = fn(v_vcf)
    assert result == expected
