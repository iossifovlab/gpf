"""
Created on Jul 5, 2018

@author: lubo
"""
import pytest


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize("variant_type,count", [
    (None, 10),
    ("sub", 9),
    ("del", 1),
    ("sub or del", 10),
])
def test_single_alt_allele_variant_types(
    variants_impl, variants, variant_type, count
):
    fvars = variants_impl(variants)("backends/effects_trio")
    vs = list(fvars.query_variants(variant_type=variant_type,))
    for v in vs:
        print(v.variant_types)
    assert len(vs) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize("variant_type,count", [
    (None, 3),
    ("sub", 2),
    ("del", 1),
    ("comp", 1),
    ("del or sub", 3),
    ("comp or sub", 3),
])
def test_multi_alt_allele_variant_types(
    variants_impl, variants, variant_type, count
):
    fvars = variants_impl(variants)("backends/effects_trio_multi")
    vs = list(fvars.query_variants(variant_type=variant_type,))
    for v in vs:
        print(v.variant_types)
    assert len(vs) == count
