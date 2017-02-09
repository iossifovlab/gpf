'''
Created on Feb 9, 2017

@author: lubo
'''


def test_dataset_ssc_load(ssc):
    assert ssc is not None
    assert ssc.denovo_studies
    assert ssc.transmitted_studies
    assert ssc.pheno_db


def test_dataset_ssc_load_families(ssc):
    families = ssc.load_families()
    assert families
