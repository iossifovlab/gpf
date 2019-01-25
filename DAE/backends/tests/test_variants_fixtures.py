'''
Created on Jun 15, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from RegionOperations import Region
from utils.vcf_utils import mat2str


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,count", [
    ("fixtures/effects_trio_multi", 3),
    ("fixtures/effects_trio", 10),
    ("fixtures/inheritance_multi", 6),
    # ("fixtures/trios2", 30),
])
def test_variants_all_count(variants_impl, variants, fixture_name, count):

    vvars = variants_impl(variants)(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        return_reference=True,
        return_unknown=True)
    vs = list(vs)
    print(vs)
    assert len(vs) == count


@pytest.mark.parametrize("fixture_name", [
    "fixtures/trios2",
])
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # FIXME: Thrift does not expect objects of type 'Region'
    # "variants_thrift",
])
def test_df_query_multiallelic3_families(
        variants_impl, variants, fixture_name):

    dfvars = variants_impl(variants)(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11606, 11606)]
    family_ids = ['f1']
    vs = dfvars.query_variants(
        regions=regions,
        family_ids=family_ids,
        return_reference=True,
        return_unknown=True)
    vs = list(vs)
    assert len(vs) == 1
    v = vs[0]

    print(v, mat2str(v.best_st))
    fa1 = v.alt_alleles[0]
    fa2 = v.alt_alleles[1]
    assert len(v.alt_alleles) == 2

    assert "mom1" in fa1.variant_in_members
    assert "dad1" in fa2.variant_in_members
    assert "ch1" not in fa1.variant_in_members
    assert "ch1" not in fa2.variant_in_members


@pytest.mark.xfail
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name", [
    "fixtures/trios2_11541",
])
def test_reference_variant(
        variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    vs = fvars.query_variants(
        return_reference=True,
        return_unknown=True
    )
    vs = list(vs)
    assert len(vs) == 2
    print(vs)

    for v in vs:
        print(v.family_id, mat2str(v.best_st))
        print(variants, "summary:", v.summary_variant)

    assert vs[0].summary_variant == vs[1].summary_variant


@pytest.mark.xfail
@pytest.mark.parametrize("variants", [
    "variants_vcf",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name", [
    "fixtures/trios2_11600",
])
def test_reference_multiallelic_variant(
        variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    vs = fvars.query_variants(
        return_reference=True,
        return_unknown=True
    )
    vs = list(vs)
    print(vs)
    assert len(vs) == 2

    for v in vs:
        print(mat2str(v.best_st))
        print("summary:", v.summary_variant)

    assert vs[0].summary_variant == vs[1].summary_variant
