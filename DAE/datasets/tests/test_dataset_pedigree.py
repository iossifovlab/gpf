'''
Created on Feb 7, 2017

@author: lubo
'''
from datasets.tests.requests import EXAMPLE_QUERY_SD


def test_get_denovo_variants_sd(sd):
    legend = sd.get_pedigree_selector(**EXAMPLE_QUERY_SD)

    vs = sd.get_denovo_variants(**EXAMPLE_QUERY_SD)

    res = [v for v in vs]
    assert 1166 == len(res)

    v = res[0]
    pedigree = v.pedigree_v3(legend)
    assert len(pedigree) == 4
    prb = pedigree[2]
    assert prb[1] == '11563.p1'
