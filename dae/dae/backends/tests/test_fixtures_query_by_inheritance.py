'''
Created on Jul 3, 2018

@author: lubo
'''
import pytest

from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize('variants', [
    'variants_impala',
    'variants_vcf'
])
@pytest.mark.parametrize("inheritance,count", [
    ("mendelian", 3),
    ("omission", 4),
    ("denovo", 2),
    ("unknown", 14),
])
def test_inheritance_trio_full(variants_impl, variants, inheritance, count):
    fvars = variants_impl(variants)("backends/inheritance_trio")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=False))
    for v in vs:
        assert len(mat2str(v.best_state)) == 7
    assert len(vs) == count


@pytest.mark.parametrize('variants', [
    'variants_impala',
    'variants_vcf'
])
@pytest.mark.parametrize("count,inheritance", [
    (7, "mendelian"),
    (1, "omission"),
    (1, "denovo"),
])
def test_inheritance_quad_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("backends/inheritance_quad")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=False))
    assert len(vs) == count
    for v in vs:
        assert len(mat2str(v.best_state)) == 9


@pytest.mark.parametrize('variants', [
    'variants_impala',
    'variants_vcf'
])
@pytest.mark.parametrize("count,inheritance", [
    (5, None),
    (4, "mendelian"),
    (0, "omission"),
    (1, "denovo"),
])
def test_inheritance_multi_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("backends/inheritance_multi")
    vs = list(fvars.query_variants(
        inheritance=inheritance,
        return_reference=False))
    for v in vs:
        for aa in v.alleles:
            print(">>", aa, aa.inheritance_in_members)
    assert len(vs) == count
