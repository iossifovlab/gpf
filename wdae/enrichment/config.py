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
    'missense',
    'synonymous'
]


class EnrichmentConfig(object):
    EFFECT_TYPES = get_effect_types(True, True)

    def __init__(self, phenotype, effect_type):
        assert phenotype in PHENOTYPES
        self.phenotype = phenotype

        et = build_effect_types_list([effect_type])
        assert 1 == len(et)
        assert all([e in self.EFFECT_TYPES for e in et])

        self.effect_type = ','.join(et)

        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'
