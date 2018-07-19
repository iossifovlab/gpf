'''
Created on Jul 18, 2018

@author: lubo
'''
import pytest

from RegionOperations import Region


@pytest.mark.parametrize(
    "regions,inheritance,effect_types,return_reference,count,matched_alleles",
    [
        ([Region("1", 878152, 878152)], None, None, True,
         1, [0, 1, 2]),
        ([Region("1", 878152, 878152)], None, None, False,
         1, [1, 2]),
        ([Region("1", 878152, 878152)], "denovo", ["synonymous"], True,
         0, None),
        ([Region("1", 878152, 878152)], "denovo", ["missense"], True,
         1, [2]),
        ([Region("1", 878152, 878152)], "mendelian", ["synonymous"], True,
         1, [1]),
        ([Region("1", 878152, 878152)], "mendelian", ["missense"], True,
         0, None),
        ([Region("1", 878152, 878152)], "mendelian", None, True,
         1, [0, 1]),
        ([Region("1", 878152, 878152)], "mendelian", None, False,
         1, [1]),
    ])
def test_f1_simple(
        variants_vcf,
        regions, inheritance, effect_types, return_reference,
        count, matched_alleles):

    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=return_reference,
        return_unknown=True)
    vs = list(vs)
    assert len(vs) == count

    for v in vs:
        print(v, v.effects, v.matched_alleles)
        assert v.matched_alleles_indexes == matched_alleles
