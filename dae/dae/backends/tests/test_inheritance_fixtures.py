# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("1", 11501, 11510), 4, "mendelian"),
        (Region("1", 11511, 11520), 5, "omission"),
        (Region("1", 11521, 11530), 4, "denovo"),
        (Region("1", 11531, 11540), 1, "unknown"),
    ],
)
def test_inheritance_trio_full(variants_vcf, region, count, inheritance):
    fvars = variants_vcf("backends/inheritance_trio")
    vs = list(
        fvars.query_variants(
            inheritance=inheritance, regions=[region], return_reference=True
        )
    )

    for v in vs:
        # assert Inheritance.from_name(inheritance) in v.inheritance_in_members
        assert len(mat2str(v.best_state)) == 7
        for a in v.alleles:
            print(">>>", a, a.inheritance_in_members)
            assert len(a.inheritance_in_members) == 3

    assert len(vs) == count


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("1", 11501, 11510), 5, "mendelian"),
        (Region("1", 11511, 11520), 3, "omission"),
        (Region("1", 11521, 11530), 2, "denovo"),
    ],
)
def test_inheritance_quad_full(variants_vcf, region, count, inheritance):
    fvars = variants_vcf("backends/inheritance_quad")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        for a in v.alt_alleles:
            print(a, mat2str(a.gt), a.members_ids, a.inheritance_in_members)
            assert len(a.inheritance_in_members) == 4
        # assert Inheritance.from_name(inheritance) in v.inheritance_in_members
        assert len(mat2str(v.best_state)) == 9


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("1", 11501, 11510), 3, "mendelian"),
        (Region("1", 11511, 11520), 1, "omission"),
        (Region("1", 11521, 11530), 1, "unknown"),
    ],
)
def test_inheritance_multi_full(variants_vcf, region, count, inheritance):
    fvars = variants_vcf("backends/inheritance_multi")
    vs = list(
        fvars.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    assert len(vs) == count
    for v in vs:
        for a in v.alt_alleles:
            print(a, mat2str(a.gt), a.members_ids, a.inheritance_in_members)
            assert len(a.inheritance_in_members) == 7
        # assert Inheritance.from_name(inheritance) in v.inheritance_in_members
        assert len(mat2str(v.best_state)) == 15
