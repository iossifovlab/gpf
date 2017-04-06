'''
Created on Mar 30, 2017

@author: lubo
'''
from pprint import pprint


def test_mother_race_filter_ssc(ssc):
    pheno_filters = ssc.descriptor['genotypeBrowser']['phenoFilters']
    for pf in pheno_filters:
        if pf['measure_type'] == 'categorical':
            mf = pf['measure_filter']
            if mf['filter_type'] == 'single':
                pprint(mf)
                assert 'domain' in mf
                pprint(mf['domain'])
