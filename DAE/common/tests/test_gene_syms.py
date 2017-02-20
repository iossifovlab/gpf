'''
Created on Feb 17, 2017

@author: lubo
'''
from common.query_base import GeneSymsMixin


def test_gene_syms_comma_separated():
    query = {'geneSymbols': 'a,b,  c  , d'}

    r = GeneSymsMixin.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])


def test_gene_syms_new_lines():
    query = {'geneSymbols': 'a,\n\rb,\n\r  c , \n\r d'}

    r = GeneSymsMixin.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])


def test_gene_weights_rvis_5():
    query = {
        'geneWeights': {
            'weight': 'RVIS_rank',
            'rangeStart': 0,
            'rangeEnd': 5
        }
    }

    r = GeneSymsMixin.get_gene_weights(**query)
    assert set(['CSMD1', 'RYR1', 'LRP1', 'PLEC', 'UBR4']) == r

    r = GeneSymsMixin.get_gene_syms(**query)
    assert set(['CSMD1', 'RYR1', 'LRP1', 'PLEC', 'UBR4']) == r


def test_empty_query():
    r = GeneSymsMixin.get_gene_syms()
    assert r is None
