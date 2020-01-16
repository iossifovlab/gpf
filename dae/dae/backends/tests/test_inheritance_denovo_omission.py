import numpy as np

from dae.variants.family_variant import FamilyAllele as FA


def test_inheritance_trio_denovo_omissions(variants_vcf):
    fvars = variants_vcf("backends/inheritance_trio_denovo_omission")
    vs = list(fvars.query_variants())

    for v in vs:
        for a in v.alleles:
            print(">>>", a, a.inheritance_in_members)
            assert len(a.inheritance_in_members) == 3

    assert len(vs) == 3


def test_inheritance_trio(variants_vcf):
    fvars = variants_vcf("backends/inheritance_trio")
    vs = list(fvars.query_variants())

    for v in vs:
        for a in v.alt_alleles:
            print(">>>", a, a.inheritance_in_members)
            assert len(a.inheritance_in_members) == 3

    assert len(vs) == 14


def test_omission_and_denovo():
    # AA,CC -> AA
    trio = [
        np.array([1, 1]),  # p1
        np.array([1, 1]),  # p2
        np.array([0, 1]),  # ch
    ]

    # FIXME:
    assert not FA.check_omission_trio(*trio, allele_index=1)
    # assert not FA.check_denovo_trio(*trio, allele_index=0)
    # assert FA.check_mendelian_trio(*trio, allele_index=0)

    assert FA.check_denovo_trio(*trio, allele_index=0)
    # assert not FA.check_denovo_trio(*trio, allele_index=1)
    # assert not FA.check_mendelian_trio(*trio, allele_index=1)
