'''
Created on Mar 23, 2018

@author: lubo
'''
from variants.summary_variant import EffectGene


def test_effect_gene_serialization():
    eg = EffectGene('a', 'b')

    assert str(eg) == 'a:b'
