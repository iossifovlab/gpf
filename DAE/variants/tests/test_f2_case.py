'''
Created on Jul 16, 2018

@author: lubo
'''
import pytest
from RegionOperations import Region


@pytest.mark.parametrize("regions,inheritance,reference, unknown, count", [
    ([Region("1", 901923, 901923)],
     None, True, True, 1),
    ([Region("1", 901923, 901923)],
     "denovo", False, False, 0),
    ([Region("1", 901923, 901923)],
     "not denovo and not omission", False, False, 0),
    ([Region("1", 901923, 901923)],
     None, True, True, 1),
    ([Region("1", 901923, 901923)],
     "omission", False, False, 0),
])
def test_f2_all_unknown(
        variants_vcf, regions, inheritance, reference, unknown, count):

    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        return_reference=reference,
        return_unknown=unknown)
    vs = list(vs)
    assert len(vs) == count
