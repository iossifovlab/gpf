'''
Created on Jul 3, 2018

@author: lubo
'''
from __future__ import print_function
import pytest

from variants.attributes import Inheritance
from variants.vcf_utils import mat2str


@pytest.mark.skip("inheritance query not ready yes")
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("inheritance,count", [
    # (Inheritance.reference, 1),
    (Inheritance.mendelian, 4),
    (Inheritance.omission, 5),
    (Inheritance.denovo, 4),
    (Inheritance.unknown, 1),
])
def test_inheritance_trio_full(variants_impl, variants, inheritance, count):
    fvars = variants_impl(variants)("fixtures/inheritance_trio")
    vs = list(fvars.query_variants(inheritance=inheritance.name))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance)
        assert v.inheritance == inheritance
        assert len(mat2str(v.best_st)) == 7


@pytest.mark.skip("inheritance query not ready yes")
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",
    # "variants_thrift",
])
@pytest.mark.parametrize("count,inheritance", [
    # (1, Inheritance.reference),
    (9, Inheritance.mendelian),
    (3, Inheritance.omission),
    (2, Inheritance.denovo),
])
def test_inheritance_quad_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("fixtures/inheritance_quad")
    vs = list(fvars.query_variants(inheritance=inheritance.name))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance)

        assert v.inheritance == inheritance
        assert len(mat2str(v.best_st)) == 9


@pytest.mark.skip("inheritance query not ready yes")
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    #     "variants_df",
    #     "variants_thrift",
])
@pytest.mark.parametrize("count,inheritance", [
    (6, None),
    (6, "mendelian"),
    (2, "omission"),
    (1, "denovo"),
])
def test_inheritance_multi_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("fixtures/inheritance_multi")
    vs = list(fvars.query_variants(inheritance=inheritance))
    for v in vs:
        print(v, mat2str(v.gt), mat2str(v.best_st), v.inheritance)

        for aa in v.alleles:
            print(">>", aa, aa.inheritance_in_members)
    assert len(vs) == count
