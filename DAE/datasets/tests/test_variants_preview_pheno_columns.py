'''
Created on Mar 23, 2017

@author: lubo
'''


from datasets.tests.requests import EXAMPLE_QUERY_SSC, EXAMPLE_QUERY_VIP
import copy


def test_get_denovo_variants_ssc_11563(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11563']

    vs = ssc.get_variants_preview(**query)
    v = vs.next()
    assert len(v) == 89
    assert 'Proband IQs NvIQ' in v
    assert 'Proband IQs vIQ' in v
    assert 'Races Mom' in v
    assert 'Races Dad' in v

    v = vs.next()
    assert len(v) == 89
    assert '11563' == v[0]


def test_get_denovo_variants_ssc_11825(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11825']

    vs = ssc.get_variants_preview(**query)
    v = vs.next()

    assert len(v) == 89
    assert 'Proband IQs NvIQ' in v
    assert 'Proband IQs vIQ' in v
    assert 'Races Mom' in v
    assert 'Races Dad' in v

    v = vs.next()
    assert len(v) == 89

    assert '11825' == v[0]


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
    assert len(v) == 89
    assert 'Proband IQs NvIQ' in v
    assert 'Proband IQs vIQ' in v

    assert len(v) == 89
    _families = vip.pheno_db.families
    count = 0
    for v in vs:
        count += 1
    assert count == 34
