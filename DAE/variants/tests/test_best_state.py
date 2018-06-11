'''
Created on Mar 19, 2018

@author: lubo
'''
from variants.vcf_utils import mat2str
from RegionOperations import Region
from variants.attributes import Inheritance


def test_trios_multi_single_allele1(single_vcf):
    fvars = single_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11500, 11500)]))
    assert len(vs) == 1
    for v in vs:
        assert v.inheritance == Inheritance.mendelian
        assert v.best_st.shape == (2, 3)
        assert len(mat2str(v.best_st)) == 7


def test_trios_multi_all_reference(single_vcf):
    fvars = single_vcf("fixtures/trios_multi")
    vs = list(fvars.query_variants(regions=[Region('1', 11502, 11502)]))
    assert len(vs) == 1
    for v in vs:
        assert v.inheritance == Inheritance.reference
        assert v.best_st.shape == (2, 3)
        assert len(mat2str(v.best_st)) == 7
