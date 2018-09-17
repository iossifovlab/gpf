'''
Created on Mar 30, 2017

@author: lubo
'''
from __future__ import unicode_literals


def test_mother_race_filter_ssc(ssc):
    pheno_filters = ssc.descriptor['genotypeBrowser']['phenoFilters']
    for pf in pheno_filters:
        if pf['measureType'] == 'categorical':
            mf = pf['measureFilter']
            if mf['filterType'] == 'single':
                assert 'domain' in mf
