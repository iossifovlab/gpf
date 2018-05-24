'''
Created on Mar 8, 2018

@author: lubo
'''
from __future__ import print_function
import numpy as np

from RegionOperations import Region
from variants.raw_vcf import RawFamilyVariants
from variants.vcf_utils import mat2str
import pytest


def test_alt_all_freq(ustudy_single):
    regions = [Region("1", 10000, 15000)]
    vs = ustudy_single.query_variants(regions=regions)

    for v in vs:
        assert 'af_alternative_allele_count' in v
        assert 'af_alternative_allele_freq' in v
        assert 'af_parents_called_count' in v
        assert 'af_parents_called_percent' in v


def test_filter_real_attr(fv_one):
    v = fv_one
    v.update_attributes({"a": [1], "b": np.array([2])})

    assert RawFamilyVariants.filter_real_attr(
        v, ['a', (1, 2), (3, 4)])

    assert RawFamilyVariants.filter_real_attr(
        v, ['a', [1, 2], [3, 4]])

    assert not RawFamilyVariants.filter_real_attr(
        v, ['a', [1.1, 2], [3, 4]])

    assert RawFamilyVariants.filter_real_attr(
        v, ['b', [1, 2], [3, 4]])


@pytest.mark.slow
def test_rare_transmitted_variants(nvcf19s):

    vs = nvcf19s.query_variants(
        inheritance='mendelian',
        real_attr_filter=['all.altFreq', (1e-8, 1)]
    )

    for c, v in enumerate(vs):
        print(c, v, v.family_id,
              v.inheritance, mat2str(v.best_st),
              v['effectType'],
              v['all.altFreq'])


@pytest.mark.slow
def test_rare_transmitted_variants_full(nvcf19f):

    vs = nvcf19f.query_variants(
        inheritance='mendelian',
        real_attr_filter=['af_alternative_allele_freq', (1e-8, 1)]
    )

    for c, v in enumerate(vs):
        print(c, v, v.family_id,
              v.inheritance, mat2str(v.best_st),
              v['effect_type'],
              v['af_alternative_allele_freq'])


def test_freq_single_family_full(full_vcf):
    fvars = full_vcf("fixtures/trios2")
    vs = fvars.query_variants(
        real_attr_filter=['af_alternative_allele_freq', (0.0001, 12.5)],
        regions=[Region("1", 11541, 11542)]
    )
    vl = list(vs)
    for v in vl:
        print(v, mat2str(v.best_st),
              v['af_alternative_allele_freq'])
    assert len(vl) == 2

    v0 = vl[0]
    v1 = vl[1]

    assert v0.family_id == 'f2'
    assert v1.family_id == 'f1'


def test_freq_single_family_simple(single_vcf):
    fvars = single_vcf("fixtures/trios2")
    vs = fvars.query_variants(
        real_attr_filter=['af_alternative_allele_freq', (0, 12.5)],
        regions=[Region("1", 11541, 11542)]
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st),
              v['af_alternative_allele_freq'])
    assert len(vl) == 2

    v0 = vl[0]
    v1 = vl[1]

    assert v0.family_id == 'f2'
    assert v1.family_id == 'f1'
