'''
Created on Mar 2, 2017

@author: lubo
'''
import copy

from datasets.tests.requests import EXAMPLE_QUERY_SSC, EXAMPLE_QUERY_VIP


def count(it):
    c = 0
    for _i in it:
        c += 1
    return c


def location_parse(location):
    chrome, pos = location.split(':')
    return chrome, int(pos)


def build_ssc_query():
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['presentInParent'] = ['mother only']
    query['presentInChild'] = ['neither']
    query['rarity'] = {
        'ultraRare': True,
    }
    query['regions'] = ['1:1,600,000-1,700,000']
    return query


def build_vip_query():
    query = copy.deepcopy(EXAMPLE_QUERY_VIP)
    del query['pedigreeSelector']
    query['presentInParent'] = ['mother only']
    query['presentInChild'] = ['neither']
    query['rarity'] = {
        'ultraRare': True,
    }
    query['limit'] = 2000
    return query


def test_transmitted_filters_ssc(ssc):
    query = build_ssc_query()

    filters = ssc.get_transmitted_filters(**query)
    print(filters)

    assert filters['presentInParent'] == ['mother only']
    assert filters['ultraRareOnly']


def test_transmitted_variants_ssc(ssc):
    query = build_ssc_query()
    vs = ssc.get_transmitted_variants(**query)
    assert vs
    res = [v for v in vs]

    assert 3 == count(res)
    for v in res:
        assert 'mom' in v.fromParentS
        chrome, pos = location_parse(v.location)
        assert chrome == '1'
        assert pos >= 1600000
        assert pos <= 1700000


QUERY = {
    'minParentsCalled': 0,
    'minAltFreqPrcnt': -1.0,
    'geneSyms': None,
    'gender': None,
    # 'study': 'VIP-JHC',
    'familyIds': None,
    'limit': 2000,
    'regionS': None,
    'effectTypes': ['splice-site', 'nonsense', 'frame-shift'],
    'inChild': None,
    'TMM_ALL': False,
    'presentInChild': ['neither'],
    'variantTypes': ['CNV', 'del', 'ins', 'sub'],
    'presentInParent': ['mother only'],
    'ultraRareOnly': True,
    'maxAltFreqPrcnt': 100.0
}
Q1 = {
    'minParentsCalled': 0,
    'minAltFreqPrcnt': -1,
    'geneSyms': None,
    'gender': None,
    # 'study': 'VIP-JHC',
    'familyIds': None,
    'limit': 2000,
    'regionS': None,
    'effectTypes': ['frame-shift', 'nonsense', 'splice-site'],
    'inChild': None,
    'TMM_ALL': False,
    'presentInChild': ['neither'],
    'variantTypes': ['CNV', 'del', 'ins', 'sub'],
    'presentInParent': ['mother only'],
    'ultraRareOnly': True,
    'maxAltFreqPrcnt': 100.0
}


# def test_transmitted_filters_vip(vip):
#     query = build_vip_query()
#     filters = vip.get_transmitted_filters(safe=True, **query)
#     print(filters)
#     for k, v in QUERY.items():
#         if k == 'effectTypes':
#             assert set(filters[k]) == set(v)
#         else:
#             assert filters[k] == v


def test_transmitted_query_vip(vip):
    query = build_vip_query()
    print(query)
    print(vip.transmitted_studies)

    vs = vip.get_transmitted_variants(**query)
    assert vs
    res = [v for v in vs]

    assert 606 == count(res)
    for v in res:
        assert 'mom' in v.fromParentS


def test_transmitted_check_vip(vip):
    st = vip.transmitted_studies[0]
    assert st
    vs = st.get_transmitted_variants(**Q1)
    res = [v for v in vs]
    assert 606 == count(res)

Q_DATASET = {
    'minParentsCalled': 0,
    'minAltFreqPrcnt': -1,
    'geneSyms': None,
    'gender': None,
    'study': 'VIP-JHC',
    'familyIds': None,
    'limit': 2000,
    'regionS': None,
    'effectTypes': ['frame-shift', 'nonsense', 'splice-site'],
    'inChild': None,
    'TMM_ALL': False,
    'presentInChild': ['neither'],
    'variantTypes': ['CNV', 'del', 'ins', 'sub'],
    'presentInParent': ['mother only'],
    'ultraRareOnly': True,
    'maxAltFreqPrcnt': 100.0
}
Q_LEGACY = {
    'minParentsCalled': 0,
    'minAltFreqPrcnt': -1,
    'geneSyms': None,
    'gender': None,
    'study': 'VIP-JHC',
    'familyIds': None,
    'limit': 2000,
    'regionS': None,
    'effectTypes': ['frame-shift', 'nonsense', 'splice-site'],
    'inChild': None,
    'TMM_ALL': False,
    'presentInChild': ['neither'],
    'variantTypes': ['CNV', 'del', 'ins', 'sub'],
    'presentInParent': ['mother only'],
    'ultraRareOnly': True,
    'maxAltFreqPrcnt': 100.0
}


Q_DENOVO_ONLY = {
    'geneSymbols': [],
    'gender': ['female', 'male'],
    'safe': True,
    'rarity': {
        'maxFreq': None,
        'minFreq': None,
        'ultraRare': None
    },
    'regions': None,
    'effectTypes': ['Nonsense', 'Frame-shift', 'Splice-site'],
    'presentInChild': None,
    'datasetId': 'VIP',
    'variantTypes': ['sub', 'ins', 'del', 'CNV'],
    'presentInParent': ['neither'],
    'geneWeights': {
        'rangeEnd': 0,
        'weight': None,
        'rangeStart': 0
    },
    'pedigreeSelector': {
        'checkedValues': ['triplication'],
        'id': '16pstatus'
    },
    'geneSet': {
        'geneSet': None,
        'geneSetsCollection': None
    }
}


def test_denovo_query_vip(vip):
    vs = vip.get_transmitted_variants(**Q_DENOVO_ONLY)
    assert vs is not None
    assert 0 == count(vs)

    vs = vip.get_variants(**Q_DENOVO_ONLY)
    assert vs is not None
    assert 1 == count(vs)
