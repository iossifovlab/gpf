'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.attributes import Inheritance


def test_trios_multi_single_allele1(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11500, 11500)]))
    assert len(vs) == 1
    for v in vs:
        print(v, v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.mendelian


def test_trios_multi_single_allele2(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11501, 11501)]))
    assert len(vs) == 1
    for v in vs:
        print(v, v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.mendelian


def test_trios_multi_all_reference(sample_vcf):
    fvars = sample_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11502, 11502)]))
    assert len(vs) == 2
    for v in vs:
        print(v, v.inheritance, v.effect_type)
        assert v.inheritance == Inheritance.reference
