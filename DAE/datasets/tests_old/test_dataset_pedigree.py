'''
Created on Feb 7, 2017

@author: lubo
'''
from datasets.tests.requests import EXAMPLE_QUERY_SD, EXAMPLE_QUERY_SSC,\
    EXAMPLE_QUERY_VIP
import copy


def test_get_denovo_variants_vip(vip):

    query = {
        "datasetId": "VIP",
        "genomicScores": [],
        "pedigreeSelector": {
            "id": "16pstatus",
            "checkedValues": [
                "triplication",
            ]
        },
        "presentInParent": {
            "presentInParent": [
                "neither"
            ],
        },
        "gender": [
            "female",
            "male",
            "unspecified"
        ],
        "variantTypes": [
            "sub",
            "ins",
            "del"
        ],
        "effectTypes": [
            "Nonsense",
            "Frame-shift",
            "Splice-site"
        ]
    }

    legend = vip.get_pedigree_selector(**query)
    assert legend is not None

    vs = vip.get_variants_preview(**query)

    res = [v for v in vs]
    assert 2 == len(res)

    vv = {k: v for (k, v) in zip(res[0], res[1])}
    print(vv)
    pedigree = vv['genotype']
    print(pedigree)

    assert len(pedigree) == 5
    p = pedigree[2]
    assert p[1] == '14752.x12'


def test_get_denovo_variants_sd(sd):
    query = copy.deepcopy(EXAMPLE_QUERY_SD)
    query['familyIds'] = ['11563']

    legend = sd.get_pedigree_selector(**query)
    vs = sd.get_denovo_variants(**query)

    res = [v for v in vs]
    assert 1 == len(res)

    v = res[0]
    pedigree = v.pedigree_v3(legend)
    assert len(pedigree) == 4
    prb = pedigree[2]
    assert prb[1] == '11563.p1'


def test_filter_families_by_pedigree_selector_all_ssc(ssc):
    family_ids = ssc.filter_families_by_pedigree_selector(**EXAMPLE_QUERY_SSC)
    assert family_ids is None


# def test_filter_families_by_pedigree_selector_autism_ssc(ssc):
#     kwargs = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     kwargs['pedigreeSelector']['checkedValues'] = ['autism']
#     family_ids = ssc.filter_families_by_pedigree_selector(**kwargs)
#     assert family_ids is not None
#     assert len(family_ids) == 2851


def test_filter_families_by_pedigree_selector_all_vip(vip):
    kwargs = copy.deepcopy(EXAMPLE_QUERY_VIP)
    kwargs['pedigreeSelector']['checkedValues'] = [
        'deletion', 'duplication', 'triplication', 'negative'
    ]
    family_ids = vip.filter_families_by_pedigree_selector(**kwargs)
    assert family_ids is None


def test_filter_families_by_pedigree_selector_triplication_vip(vip):
    kwargs = copy.deepcopy(EXAMPLE_QUERY_VIP)
    kwargs['pedigreeSelector']['checkedValues'] = [
        'triplication'
    ]
    family_ids = vip.filter_families_by_pedigree_selector(**kwargs)
    assert family_ids is not None
    assert len(family_ids) == 2


def test_get_family_ids_all_vip(vip):
    kwargs = copy.deepcopy(EXAMPLE_QUERY_VIP)
    kwargs['pedigreeSelector']['checkedValues'] = [
        'deletion', 'duplication', 'triplication', 'negative'
    ]
    family_ids = vip.get_family_ids(**kwargs)
    assert family_ids is None
