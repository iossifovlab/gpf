'''
Created on Jul 3, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from utils.vcf_utils import mat2str


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",  # FIXME:
    "variants_thrift",
])
@pytest.mark.parametrize("inheritance,count", [
    ("mendelian", 14),
    ("omission", 5),
    ("denovo", 4),
    ("unknown", 15),
])
def test_inheritance_trio_full(variants_impl, variants, inheritance, count):
    fvars = variants_impl(variants)("fixtures/inheritance_trio")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=True))
    for v in vs:
        # FIXME:
        # assert Inheritance.from_name(inheritance) in v.inheritance_in_members
        assert len(mat2str(v.best_st)) == 7
    assert len(vs) == count


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",  # FIXME:
    "variants_thrift",
])
@pytest.mark.parametrize("count,inheritance", [
    (11, "mendelian"),
    (3, "omission"),
    (2, "denovo"),
])
def test_inheritance_quad_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("fixtures/inheritance_quad")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=True))
    assert len(vs) == count
    for v in vs:
        assert len(mat2str(v.best_st)) == 9


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",  # FIXME:
    "variants_thrift",
])
@pytest.mark.parametrize("count,inheritance", [
    (6, None),
    (6, "mendelian"),
    (2, "omission"),
    (1, "denovo"),
])
def test_inheritance_multi_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("fixtures/inheritance_multi")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=True))
    for v in vs:
        for aa in v.alleles:
            print(">>", aa, aa.inheritance_in_members)
    assert len(vs) == count
