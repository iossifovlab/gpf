'''
Created on Jul 5, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
@pytest.mark.parametrize("variant_type,count", [
    (None, 10),
    ('sub', 9),
    ('del', 1),
    ('sub or del', 10),
])
def test_single_alt_allele_variant_types(
        variants_impl, variants, variant_type, count):
    fvars = variants_impl(variants)("fixtures/effects_trio")
    vs = list(fvars.query_variants(
        variant_type=variant_type,
    ))
    for v in vs:
        print(v.variant_types)
    assert len(vs) == count


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_impala",
])
@pytest.mark.parametrize("variant_type,count", [
    (None, 3),
    ('sub', 3),
    ('del', 1),
    ('del or sub', 3),
])
def test_multi_alt_allele_variant_types(
        variants_impl, variants, variant_type, count):
    fvars = variants_impl(variants)("fixtures/effects_trio_multi")
    vs = list(fvars.query_variants(
        variant_type=variant_type,
    ))
    for v in vs:
        print(v.variant_types)
    assert len(vs) == count
