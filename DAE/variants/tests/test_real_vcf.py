'''
Created on Mar 5, 2018

@author: lubo
'''
from variants.variant import mat2str


def test_rvcf_config(rvcf_config):

    print(rvcf_config)
    assert rvcf_config is not None


def test_rvcf_init(rvcf):

    assert rvcf is not None

    for v in rvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st))
