'''
Created on Nov 15, 2016

@author: lubo
'''
from DAE import vDB
from Variant import variantInMembers


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


def test_experiment_denovo_variants_by_person_id():
    query = {
        'familyIds': None,
        'gender': None,
        'geneSyms': set(['POGZ']),
        'regionS': None,
        'effectTypes': ['missense'],
        'inChild': 'prb',
        'limit': None,
        'variantTypes': None,
        'presentInParent': ['neither'],
        'presentInChild': None,
    }
    st = vDB.get_study('w1202s766e611')
    vit = st.get_transmitted_variants(**query)
    variants = [vs for vs in vit]
    assert 0 == len(variants)

    st = vDB.get_study('IossifovWE2014')
    assert st is not None
    vit = st.get_denovo_variants(**query)
    variants = [vs for vs in vit]
    assert 2 == len(variants)
    v1 = variants[0]
    v2 = variants[1]

    #     print(' ')
    #     print(v1._memberInOrder)
    #     print(v1._bestSt)
    #     print(variantInMembers(v1))
    #     print(' ')
    #     print(v2._memberInOrder)
    #     print(v2._bestSt)
    #     print(variantInMembers(v2))
    #     print(' ')
    #     print(dir(v1))

    ps = variantInMembers(v1)
    assert 1 == len(ps)
    assert '14551.p1' == ps[0]

    ps = variantInMembers(v2)
    assert 1 == len(ps)
    assert '14483.p1' == ps[0]
