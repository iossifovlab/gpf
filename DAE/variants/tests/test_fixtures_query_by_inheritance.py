'''
Created on Jul 3, 2018

@author: lubo
'''
from __future__ import print_function
import pytest

from variants.attributes import Inheritance
from variants.vcf_utils import mat2str


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("inheritance,count", [
    (Inheritance.reference, 1),
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
