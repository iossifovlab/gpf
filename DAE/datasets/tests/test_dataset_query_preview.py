'''
Created on Feb 7, 2017

@author: lubo
'''
from datasets.tests.requests import EXAMPLE_QUERY_SD


def test_get_denovo_variants_sd(sd):
    vs = sd.get_variants_preview(**EXAMPLE_QUERY_SD)
    v = vs.next()
    print(v)
    v = vs.next()
    print(v)
