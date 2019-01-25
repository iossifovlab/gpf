'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

from RegionOperations import Region
from utils.vcf_utils import mat2str


def test_trios_multi_single_allele1_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11500, 11500)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (3, 3)


def test_trios_multi_single_allele2_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11501, 11501)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        assert v.best_st.shape == (3, 3)


def test_trios_multi_all_reference_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11502, 11502)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (3, 3)


def test_trios_multi_unknown_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11503, 11503)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (3, 3)


def test_trios_multi_multi_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11504, 11504)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (3, 3)


def test_trios_multi_multi3_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11505, 11505)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (4, 3)

    fvars = variants_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11506, 11506)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        print(mat2str(v.best_st))
        assert v.best_st.shape == (4, 3)
