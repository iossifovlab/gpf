'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function
from variants.vcf_utils import mat2str
import pytest
from variants.raw_vcf import RawFamilyVariants


def test_nvcf_config(nvcf_config):
    print(nvcf_config)
    assert nvcf_config is not None


@pytest.mark.slow
def test_nvcf_all_variants(nvcf):
    assert nvcf is not None

    for v in nvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st),
              v.inheritance)


@pytest.mark.slow
def test_uvcf_all_variants(uvcf):
    for v in uvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st), v.inheritance)


@pytest.mark.veryslow
def test_fvcf_all_variants(fvcf):
    for v in fvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st), v.inheritance)


@pytest.mark.slow
@pytest.mark.parametrize("region", [
    'MT',
    'GL000207.1',
    'GL000226.1',
    'GL000229.1',
    'GL000231.1',
    'GL000210.1', 'GL000239.1', 'GL000235.1', 'GL000201.1', 'GL000247.1',
    'GL000245.1',
    'GL000197.1', 'GL000203.1', 'GL000246.1', 'GL000249.1', 'GL000196.1',
    'GL000248.1', 'GL000244.1', 'GL000238.1', 'GL000202.1', 'GL000234.1',
    'GL000232.1', 'GL000206.1', 'GL000240.1', 'GL000236.1', 'GL000241.1',
    'GL000243.1', 'GL000242.1', 'GL000230.1', 'GL000237.1', 'GL000233.1',
    'GL000204.1', 'GL000198.1', 'GL000208.1', 'GL000191.1', 'GL000227.1',
    'GL000228.1', 'GL000214.1', 'GL000221.1', 'GL000209.1', 'GL000218.1',
    'GL000220.1', 'GL000213.1', 'GL000211.1', 'GL000199.1', 'GL000217.1',
    'GL000216.1', 'GL000215.1', 'GL000205.1', 'GL000219.1', 'GL000224.1',
    'GL000223.1', 'GL000195.1', 'GL000212.1', 'GL000222.1', 'GL000200.1',
    'GL000193.1', 'GL000194.1', 'GL000225.1', 'GL000192.1', 'phiX'
])
def test_raw_vcf_on_empty_region(vcf19_config, composite_annotator, region):
    fvars = RawFamilyVariants(
        vcf19_config, region=region, annotator=composite_annotator)

    assert fvars.is_empty()

    count = 0
    for vs in fvars.query_variants():
        for v in vs:
            print(v)
            count += 1
    assert count == 0
