'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import unicode_literals
from datasets.dataset import Dataset


def test_gene_syms_comma_separated():
    query = {'geneSymbols': 'a,b,  c  , d'}

    r = Dataset.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])


def test_gene_syms_new_lines():
    query = {'geneSymbols': 'a,\n\rb,\n\r  c , \n\r d'}

    r = Dataset.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])


def test_gene_weights_rvis_5():
    query = {
        'geneWeights': {
            'weight': 'RVIS_rank',
            'rangeStart': 0,
            'rangeEnd': 5.01
        }
    }

    r = Dataset.get_gene_weights(**query)
    assert set(['CSMD1', 'RYR1', 'LRP1', 'PLEC', 'UBR4']) == r

    r = Dataset.get_gene_weights(**query)
    assert set(['CSMD1', 'RYR1', 'LRP1', 'PLEC', 'UBR4']) == r


def test_empty_query():
    r = Dataset.get_gene_symbols()
    assert r is not None
