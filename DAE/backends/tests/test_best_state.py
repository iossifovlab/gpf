'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import
from utils.vcf_utils import mat2str
from RegionOperations import Region


def test_trios_multi_single_allele1(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11500, 11500)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        assert v.best_st.shape == (3, 3)
        assert len(mat2str(v.best_st)) == 11


def test_trios_multi_all_reference(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    vs = list(fvars.query_variants(
        regions=[Region('1', 11502, 11502)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    for v in vs:
        assert v.best_st.shape == (3, 3)
        assert len(mat2str(v.best_st)) == 11
