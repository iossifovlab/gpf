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
    ssc.load_families()
    assert ssc.families
    assert ssc.persons


def test_dataset_vip_supplement_pedigree_selector(vip):
    assert vip is not None
    vip.load_families()
    vip.load_pedigree_selectors()

    for p in vip.persons.values():
        assert p.atts['16pstatus']
