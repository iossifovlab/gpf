'''
Created on Feb 17, 2017

@author: lubo
'''


def test_phenotypes_ssc(ssc):
    phenotypes = ssc.get_phenotypes()
    assert ['autism', 'unaffected'] == phenotypes


def test_phenotypes_sd(sd):
    phenotypes = sd.get_phenotypes()
    assert [
        'autism',
        'congenital_heart_disease',
        'epilepsy',
        'intellectual_disability',
        'schizophrenia',
        'unaffected'
    ] == phenotypes


def test_phenotypes_vip(vip):
    phenotypes = vip.get_phenotypes()
    assert ['ASD and other neurodevelopmental disorders', 'unaffected'] == \
        phenotypes
