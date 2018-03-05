'''
Created on Mar 5, 2018

@author: lubo
'''


def test_rvcf_config(rvcf_config):

    print(rvcf_config)
    assert rvcf_config is not None


def test_rvcf_init(rvcf):

    assert rvcf is not None
