'''
Created on Mar 3, 2017

@author: lubo
'''


def test_ssc_created(ssc):
    assert ssc is not None


def test_ssc_family_queries_categorical(ssc):
    family_ids = ssc.get_families_by_measure_categorical(
        'pheno_common.race', ['native-hawaiian'])
    assert 11 == len(family_ids)


def test_ssc_family_queries_continuous(ssc):
    family_ids = ssc.get_families_by_measure_continuous(
        'ssc_commonly_used.head_circumference', 49, 50, roles=['prb'])
    assert family_ids is not None
