'''
Created on Apr 5, 2018

@author: lubo
'''
from __future__ import print_function
from variants.vcf_utils import mat2str
import pytest


@pytest.mark.skip
@pytest.mark.parametrize("family_ids", [
    ['12901'],
    ['13632'],
    ['11391'],
])
def test_check_overlap1(data_vcf19, family_ids):
    fvars = data_vcf19("ssc_nygc2/overlap1")
    assert fvars is not None

    print("overlap1", *family_ids)
    for v in fvars.query_variants(
            inheritance="not reference",
            family_ids=family_ids,
    ):
        print(
            v, mat2str(v.gt), mat2str(v.best_st),
            ",".join([p.sample_id for p in v.members_in_order]))
        for aa in v.falt_alleles:
            print("\t", aa, ":>", v.alt_details[aa])


@pytest.mark.skip
@pytest.mark.parametrize("family_ids", [
    ['13632'],
    ['13659'],
    ['12901']
])
def test_check_overlap2(data_vcf19, family_ids):
    fvars = data_vcf19("ssc_nygc2/overlap2")
    assert fvars is not None

    print("overlap2")
    for v in fvars.query_variants(
            inheritance="not reference",
            family_ids=family_ids,
    ):
        print(
            v, mat2str(v.gt), mat2str(v.best_st),
            ",".join([p.sample_id for p in v.members_in_order]))
        for aa in v.falt_alleles:
            print("\t", aa, ":>", v.alt_details[aa])


@pytest.mark.skip
@pytest.mark.parametrize("family_ids", [
    ['12901'],
    ['11391'],
])
def test_check_overlap1_12901_11391_simple(data_vcf19, family_ids):
    fvars = data_vcf19("ssc_nygc2/overlap1_12901_11391_simple")
    assert fvars is not None

    print("overlap1")
    for v in fvars.query_variants(
            inheritance="not reference",
            family_ids=family_ids,
    ):
        print(
            v, mat2str(v.gt), mat2str(v.best_st),
            ",".join([p.sample_id for p in v.members_in_order]))
        for aa in v.falt_alleles:
            print("\t", aa, ":>", v.alt_details[aa])
