'''
Created on Jun 11, 2015

@author: lubo
'''
from VariantAnnotation import get_effect_types
from query_prepare import build_effect_types_list

PHENOTYPES = [
    'autism',
    'congenital heart disease',
    'epilepsy',
    'intelectual disability',
    'schizophrenia',
    'unaffected',
]

EFFECT_TYPES = [
    'LGDs',
    'Missense',
    'Synonymous'
]


class EnrichmentConfig(object):
    EFFECT_TYPES = get_effect_types(True, True)

    def __init__(self, phenotype, effect_type):
        assert phenotype in PHENOTYPES
        self.phenotype = phenotype

        self.effect_type = build_effect_types_list([effect_type])

        assert all([et in self.EFFECT_TYPES for et in self.effect_type])
        self.effect_type = ','.join(self.effect_type)

        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'

#     def build_label(self, gender=None, rec=None):
#         spec = self.build_spec(gender, rec)
#         return spec['label']
#
#     def build_spec(self, gender=None, rec=None):
#         def expand_effect(et):
#             if 'lgds' == et.lower():
#                 return 'Nonsense,Frame-shift,Splice-site'
#             if 'missense' == et.lower():
#                 return 'Missense'
#             if 'sysnonymous' == et.lower():
#                 return 'Synonymous'
#             raise ValueError("bad effect type: {}".format(et))
#
#         result = {}
#         result['effect'] = self.effect_types
#         print(self.effect_types)
#
#         if rec:
#             result['type'] = 'rec'
#             name = 'Rec {}'.format(self.effect_types)
#         else:
#             result['type'] = 'event'
#             name = self.effect_types
#
#         if gender:
#             result['gender'] = 'male,female'
#             result['inchild'] = self.in_child
#         elif gender == 'M':
#             result['gender'] = 'male'
#             result['inchild'] = self.in_child + 'M'
#         elif gender == 'F':
#             result['gender'] = 'female'
#             result['inchild'] = self.in_child + 'F'
#         else:
#             raise ValueError("bad gender: {}".format(gender))
#
#         label = "{}|{}|{}|{}|{}".format(
#             self.in_child,
#             name,
#             self.in_child,
#             result['gender'],
#             expand_effect(self.effect_types)
#         )
#         result['label'] = label
#         return result

# class EnrichmentResult(EnrichmentConfig):
#
#     def __init__(self, phenotype, effect_types):
#         super(EnrichmentResult, self).__init__(phenotype, effect_types)
#         self.total_events = -1
#         self.total_events_male = -1
#         self.total_events_female = -1
#
#         self.events_in_affected_genes = -1
#         self.events_in_affected_genes_male = -1
#         self.events_in_affected_genes_female = -1


PRB_TESTS_SPECS = [
    # 0
    {'label': 'prb|Rec LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
     'type': 'rec',
     'inchild': 'prb',
     'effect': 'LGDs'},
    # 1
    {'label': 'prb|LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'prb',
     'effect': 'LGDs'},
    # 2
    {'label': 'prb|Male LGDs|prb|male|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'prbM',
     'effect': 'LGDs'},
    # 3
    {'label': 'prb|Female LGDs|prb|female|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'prbF',
     'effect': 'LGDs'},
    # 4
    {'label': 'prb|Rec Missense|prb|male,female|Missense',
     'type': 'rec',
     'inchild': 'prb',
     'effect': 'missense'},
    # 5
    {'label': 'prb|Missense|prb|male,female|Missense',
     'type': 'event',
     'inchild': 'prb',
     'effect': 'missense'},
    # 6
    {'label': 'prb|Male Missense|prb|male|Missense',
     'type': 'event',
     'inchild': 'prbM',
     'effect': 'missense'},
    # 7
    {'label': 'prb|Female Missense|prb|female|Missense',
     'type': 'event',
     'inchild': 'prbF',
     'effect': 'missense'},
    # 8
    {'label': 'prb|Rec Synonymous|prb|male,female|Synonymous',
     'type': 'rec',
     'inchild': 'prb',
     'effect': 'synonymous'},
    # 9
    {'label': 'prb|Synonymous|prb|male,female|Synonymous',
     'type': 'event',
     'inchild': 'prb',
     'effect': 'synonymous'},
    # 10
    {'label': 'prb|Male Synonymous|prb|male|Synonymous',
     'type': 'event',
     'inchild': 'prbM',
     'effect': 'synonymous'},
    # 11
    {'label': 'prb|Female Synonymous|prb|female|Synonymous',
     'type': 'event',
     'inchild': 'prbF',
     'effect': 'synonymous'},

]

SIB_TESTS_SPECS = [
    # 0
    {'label': 'sib|Rec LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site',
     'type': 'rec',
     'inchild': 'sib',
     'effect': 'LGDs'},
    # 1
    {'label': 'sib|LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'sib',
     'effect': 'LGDs'},
    # 2
    {'label': 'sib|Male LGDs|sib|male|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'sibM',
     'effect': 'LGDs'},
    # 3
    {'label': 'sib|Female LGDs|sib|female|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'sibF',
     'effect': 'LGDs'},
    # 4
    {'label': 'sib|Rec Missense|sib|male,female|Missense',
     'type': 'rec',
     'inchild': 'sib',
     'effect': 'missense'},
    # 5
    {'label': 'sib|Missense|sib|male,female|Missense',
     'type': 'event',
     'inchild': 'sib',
     'effect': 'missense'},
    # 6
    {'label': 'sib|Male Missense|sib|male|Missense',
     'type': 'event',
     'inchild': 'sibM',
     'effect': 'missense'},
    # 7
    {'label': 'sib|Female Missense|sib|female|Missense',
     'type': 'event',
     'inchild': 'sibF',
     'effect': 'missense'},
    # 8
    {'label': 'sib|Rec Synonymous|sib|male,female|Synonymous',
     'type': 'rec',
     'inchild': 'sib',
     'effect': 'synonymous'},
    # 9
    {'label': 'sib|Synonymous|sib|male,female|Synonymous',
     'type': 'event',
     'inchild': 'sib',
     'effect': 'synonymous'},
    # 10
    {'label': 'sib|Male Synonymous|sib|male|Synonymous',
     'type': 'event',
     'inchild': 'sibM',
     'effect': 'synonymous'},
    # 11
    {'label': 'sib|Female Synonymous|sib|female|Synonymous',
     'type': 'event',
     'inchild': 'sibF',
     'effect': 'synonymous'},
]
