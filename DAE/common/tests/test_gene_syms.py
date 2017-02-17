'''
Created on Feb 17, 2017

@author: lubo
'''
from common.query_base import GeneSymsBase


def test_gene_syms_comma_separated():
    query = {'geneSymbols': 'a,b,  c  , d'}

    r = GeneSymsBase.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])


def test_gene_syms_new_lines():
    query = {'geneSymbols': 'a,\n\rb,\n\r  c , \n\r d'}

    r = GeneSymsBase.get_gene_symbols(**query)

    assert r == set(['a', 'b', 'c', 'd'])
