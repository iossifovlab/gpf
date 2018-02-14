'''
Created on Feb 14, 2018

@author: lubo
'''
from __future__ import print_function
from RegionOperations import Region


def test_mendelian(uagre):
    df = uagre.query_regions([Region("1", 11541, 54721)])

    res_df, variants = uagre.query_families(['AU1921'], df)
    assert len(res_df) == 5
    assert len(variants) == 5

    for vs in variants.values():
        for v in vs:
            print(v, v.is_medelian(), v.effect_type)
            print(v.best_st)
            print(v.gt)
