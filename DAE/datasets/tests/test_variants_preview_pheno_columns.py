'''
Created on Mar 23, 2017

@author: lubo
'''


from datasets.tests.requests import EXAMPLE_QUERY_SSC, EXAMPLE_QUERY_VIP
from pprint import pprint
import copy


def test_get_denovo_variants_ssc_11563(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11563']

    vs = ssc.get_variants_preview(**query)
    v = vs.next()
    pprint(v)
    assert len(v) == 33
    nviq, viq, mom, dad = v[-4:]
    assert 'Proband IQs.NvIQ' == nviq
    assert 'Proband IQs.vIQ' == viq
    assert 'Races.Mom' == mom
    assert 'Races.Dad' == dad

    v = vs.next()
    pprint(v)

    assert len(v) == 33

    assert '11563' == v[0]

    nviq, viq, mom, dad = v[-4:]
    assert '101.0' == nviq
    assert '110.0' == viq
    assert 'white' == mom
    assert 'asian' == dad


def test_get_denovo_variants_ssc_11825(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11825']

    vs = ssc.get_variants_preview(**query)
    v = vs.next()
    pprint(v)
    assert len(v) == 33
    nviq, viq, mom, dad = v[-4:]
    assert 'Proband IQs.NvIQ' == nviq
    assert 'Proband IQs.vIQ' == viq
    assert 'Races.Mom' == mom
    assert 'Races.Dad' == dad

    v = vs.next()
    pprint(v)

    assert len(v) == 33

    assert '11825' == v[0]

    nviq, viq, mom, dad = v[-4:]
    assert '135.0' == nviq
    assert '115.0' == viq
    assert 'white' == mom
    assert 'white' == dad


def test_get_denovo_variants_vip(vip):
    query = copy.deepcopy(EXAMPLE_QUERY_VIP)
    query['presentInParent'] = ['neither']
    query['pedigreeSelector'] = {
        'id': "16pstatus",
        'checkedValues': [
            'deletion', 'duplication', 'triplication', 'negative'
        ]
    }

    vs = vip.get_variants_preview(**query)
    v = vs.next()
    pprint(v)
    assert len(v) == 33
    nviq, viq, status, diagnossis = v[-4:]
    assert 'Proband IQs.NvIQ' == nviq
    assert 'Proband IQs.vIQ' == viq
    assert 'Status.16p' == status
    assert 'Status.Diagnosis' == diagnossis

    assert len(v) == 33
    families = vip.pheno_db.families
    print(families.keys())
    count = 0
    for v in vs:
        count += 1
    assert count == 18

#     pprint(v)
#
#     assert len(v) == 32
#     nviq, viq, status = v[-3:]
#     print(nviq, viq, status)
#
#     assert '110.0' == nviq
#     assert '76.0' == viq
#     assert 'deletion' == status
