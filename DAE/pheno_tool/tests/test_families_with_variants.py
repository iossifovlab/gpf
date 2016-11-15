'''
Created on Nov 15, 2016

@author: lubo
'''
from DAE import vDB


def test_experiment_with_mysql_families_with_variants():
    query = {
        'minParentsCalled': 0,
        'minAltFreqPrcnt': -1.0,
        'familyIds': None,
        'gender': None,
        'geneSyms': set(['POGZ']),
        'ultraRareOnly': False,
        'regionS': None,
        'effectTypes': ['missense'],
        'inChild': 'prb',
        'limit': None,
        'variantTypes': None,
        'presentInParent': ['father only'],
        'TMM_ALL': False,
        'presentInChild': None,
        'maxAltFreqPrcnt': 100.0}
    st = vDB.get_study('w1202s766e611')

    fit = st.get_families_with_transmitted_variants(**query)
    families = [f for f in fit]
    assert 42 == len(families)


def test_experiment_with_mysql_families_with_variants_all():
    query = {
        'minParentsCalled': 0,
        'minAltFreqPrcnt': -1.0,
        'familyIds': None,
        'gender': None,
        'ultraRareOnly': False,
        'regionS': None,
        'effectTypes': ["no-frame-shift-newStop",
                        "frame-shift", "nonsense", "splice-site"],
        'inChild': 'prb',
        'limit': None,
        'variantTypes': None,
        'presentInParent': ['father only'],
        'TMM_ALL': False,
        'presentInChild': None,
        'maxAltFreqPrcnt': 100.0}
    st = vDB.get_study('w1202s766e611')

    fit = st.get_families_with_transmitted_variants(**query)
    families = [f for f in fit]
    assert 2462 == len(families)
