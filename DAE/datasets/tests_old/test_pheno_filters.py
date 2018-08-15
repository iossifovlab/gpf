'''
Created on Mar 25, 2017

@author: lubo
'''
from __future__ import unicode_literals
import copy
from datasets.tests.requests import EXAMPLE_QUERY_SSC, EXAMPLE_QUERY_VIP


# def test_verbal_iq_interval_ssc(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'continuous',
#             'measure': 'ssc_core_descriptive.ssc_diagnosis_verbal_iq',
#             'role': 'prb',
#             'mmin': 10,
#             'mmax': 11.1
#         }
#     ]
#     res = ssc.get_family_pheno_filters(**query)
#     assert len(res) == 1
# 
#     assert len(res[0]) == 15
# 
# 
# def test_head_circumference_interval(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'continuous',
#             'measure': 'ssc_commonly_used.head_circumference',
#             'role': 'prb',
#             'mmin': 49,
#             'mmax': 50.1
#         }
#     ]
#     res = ssc.get_family_pheno_filters(**query)
#     assert len(res) == 1
# 
#     assert len(res[0]) == 102
# 
# 
# def test_categorical_measure_filter_race_hawaiian(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'categorical',
#             'measure': 'pheno_common.race',
#             'role': 'prb',
#             'selection': ['native-hawaiian'],
#         }
#     ]
#     res = ssc.get_family_pheno_filters(**query)
#     assert len(res) == 1
#     assert len(res[0]) == 1
# 
# 
# def test_categorical_measure_filter_race_native_american(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'categorical',
#             'measure': 'pheno_common.race',
#             'role': 'prb',
#             'selection': ['native-american'],
#         }
#     ]
#     res = ssc.get_family_pheno_filters(**query)
#     assert len(res) == 1
#     assert len(res[0]) == 2
# 
# 
# def test_head_circumference_interval_variants(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'continuous',
#             'measure': 'ssc_commonly_used.head_circumference',
#             'role': 'prb',
#             'mmin': 49,
#             'mmax': 50.1
#         }
#     ]
#     vs = ssc.get_variants(**query)
#     assert vs is not None
# 
#     assert 19 == len(list(vs))
# 
# 
# def test_categorical_measure_filter_race_hawaiian_variants(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'categorical',
#             'measure': 'pheno_common.race',
#             'role': 'prb',
#             'selection': ['native-hawaiian'],
#         }
#     ]
#     query['familyIds'] = ['11483']
# 
#     vs = ssc.get_variants(**query)
#     vs = list(vs)
# #     assert len(vs) == 1
# #     assert vs[0].familyId == '11483'
# 
# 
# def test_pheno_filter_combine_variants(ssc):
#     query = copy.deepcopy(EXAMPLE_QUERY_SSC)
#     query['phenoFilters'] = [
#         {
#             'measureType': 'categorical',
#             'measure': 'pheno_common.race',
#             'role': 'dad',
#             'selection': ['native-hawaiian'],
#         },
#         {
#             'measureType': 'continuous',
#             'measure': 'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
#             'role': 'prb',
#             'mmin': 80,
#             'mmax': 80.1
#         }
#     ]
# 
#     vs = ssc.get_variants(**query)
#     vs = list(vs)
#     assert len(vs) == 1
#     assert vs[0].familyId == '11483'
# 
# 
# def test_pheno_filters_combine_categorical(ssc):
#     query = {
#         u'phenoFilters': [
#             {
#                 u'selection': [
#                     u'native-american'
#                 ],
#                 u'measureType': u'categorical',
#                 u'role': u'mom',
#                 u'id': u'Mother Race',
#                 u'measure': u'pheno_common.race'
#             },
#             {
#                 u'selection': [
#                     u'native-american'
#                 ],
#                 u'measureType': u'categorical',
#                 u'role': u'dad',
#                 u'id': u'Father Race',
#                 u'measure': u'pheno_common.race'
#             }],
#         u'gender': [
#             u'female',
#             u'male'
#         ],
#         'safe': True,
#         u'effectTypes': [
#             u'Nonsense',
#             u'Frame-shift',
#             u'Splice-site',
#             u'Missense',
#         ],
#         u'presentInChild': [
#             u'affected only',
#             u'affected and unaffected'
#         ],
#         u'variantTypes': [
#             u'sub', u'ins', u'del', u'CNV'
#         ],
#         u'presentInParent': {
#             u'rarity': {
#                 u'maxFreq': None,
#                 u'minFreq': None,
#                 u'ultraRare': True
#             },
#             u'presentInParent': [
#                 u'neither'
#             ]},
#         'limit': 2000,
#         u'datasetId': u'SSC'
#     }
#     vs = ssc.get_variants(**query)
#     vs = list(vs)
#     assert len(vs) == 1
#     assert '11142' == vs[0].familyId
# 
# 
# def test_pheno_filters_combine_categorical_q2(ssc):
#     query = {
#         u'phenoFilters': [
#             {u'selection': [u'native-hawaiian'],
#              u'measureType': u'categorical',
#              u'role': u'mom',
#              u'id': u'Mother Race',
#              u'measure': u'pheno_common.race'
#              },
#             {
#                 u'selection': [u'native-american'],
#                 u'measureType': u'categorical',
#                 u'role': u'dad',
#                 u'id': u'Father Race',
#                 u'measure': u'pheno_common.race'
#             }
#         ],
#         u'gender': [
#             u'female', u'male'
#         ],
#         'safe': True,
#         u'effectTypes': [
#             u'Nonsense', u'Frame-shift', u'Splice-site'
#         ],
#         u'presentInChild': [
#             u'affected only', u'affected and unaffected'
#         ],
#         u'variantTypes': [
#             u'sub', u'ins', u'del', u'CNV'
#         ],
#         u'presentInParent': {
#             u'rarity': {
#                 u'maxFreq': None, u'minFreq': None, u'ultraRare': True
#             },
#             u'presentInParent': [u'neither']
#         },
#         'limit': 2000,
#         u'datasetId': u'SSC'
#     }
#     vs = ssc.get_variants(**query)
#     vs = list(vs)
#     assert len(vs) == 0


def test_verbal_iq_interval_vip(vip):

    query = copy.deepcopy(EXAMPLE_QUERY_VIP)
    query['phenoFilters'] = [
        {
            'measureType': 'continuous',
            'measure': 'diagnosis_summary.best_nonverbal_iq',
            'role': 'prb',
            'mmin': 51,
            'mmax': 51.1
        }
    ]
    query['effectTypes'] = [
        'Missense',
    ]
    query["presentInParent"] = [
        "neither"
    ]
    del query['pedigreeSelector']

    vs = vip.get_variants(**query)
    vs = list(vs)
    assert len(vs) == 2
    assert vs[0].familyId == '14904.x3-14904.x6'
