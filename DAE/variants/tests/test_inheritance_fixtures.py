'''
Created on Mar 20, 2018

@author: lubo
'''
from __future__ import print_function

import pytest
from RegionOperations import Region
from variants.attributes import Inheritance
from variants.vcf_utils import mat2str


@pytest.mark.parametrize("region,count,inheritance", [
    (Region('1', 11500, 11500), 1, Inheritance.reference),
    (Region('1', 11501, 11510), 4, Inheritance.mendelian),
    (Region('1', 11511, 11520), 5, Inheritance.omission),
    (Region('1', 11521, 11530), 4, Inheritance.denovo),
    (Region('1', 11531, 11540), 1, Inheritance.unknown),
])
def test_inheritance_trio(simple_vcf, region, count, inheritance):
    fvars = simple_vcf("fixtures/inheritance_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)
        assert v.inheritance == inheritance
        assert len(mat2str(v.best_st)) == 7


@pytest.mark.parametrize("region,count,inheritance", [
    (Region('1', 11500, 11500), 1, Inheritance.reference),
    (Region('1', 11501, 11510), 5, Inheritance.mendelian),
    (Region('1', 11511, 11520), 3, Inheritance.omission),
    (Region('1', 11521, 11530), 2, Inheritance.denovo),
])
def test_inheritance_quad(simple_vcf, region, count, inheritance):
    fvars = simple_vcf("fixtures/inheritance_quad")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)

        assert v.inheritance == inheritance
        assert len(mat2str(v.best_st)) == 9


@pytest.mark.parametrize("region,count,inheritance", [
    (Region('1', 11500, 11500), 1, Inheritance.reference),
    (Region('1', 11501, 11510), 3, Inheritance.mendelian),
    (Region('1', 11511, 11520), 1, Inheritance.omission),
    (Region('1', 11521, 11530), 1, Inheritance.other),
])
def test_inheritance_multi(simple_vcf, region, count, inheritance):
    fvars = simple_vcf("fixtures/inheritance_multi")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance, v.effect_type)

        assert v.inheritance == inheritance
        assert len(mat2str(v.best_st)) == 15
