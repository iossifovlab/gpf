'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.attributes import Inheritance
from variants.vcf_utils import mat2str


def test_trios_multi_single_allele1(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11500, 11500)]))
    assert len(vs) == 1
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.mendelian
        assert v.best_st.shape == (2, 3)


def test_trios_multi_single_allele2(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11501, 11501)]))
    assert len(vs) == 1
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.mendelian
        assert v.best_st.shape == (2, 3)


def test_trios_multi_all_reference(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11502, 11502)]))
    assert len(vs) == 2
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.reference
        assert v.best_st.shape == (2, 3)


def test_trios_multi_unknown(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11503, 11503)]))
    assert len(vs) == 2
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.unknown
        assert v.best_st.shape == (2, 3)


def test_trios_multi_multi(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11504, 11504)]))
    assert len(vs) == 2
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.unknown
        assert v.best_st.shape == (2, 3)


def test_trios_multi_multi3(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11505, 11505)]))
    assert len(vs) == 3
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.unknown
        assert v.best_st.shape == (2, 3)

    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11506, 11506)]))
    assert len(vs) == 2
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.unknown
        assert v.best_st.shape == (2, 3)
