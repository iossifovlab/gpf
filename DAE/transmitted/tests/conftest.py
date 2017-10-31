'''
Created on May 22, 2017

@author: lubo
'''
import pytest
from gene.gene_set_collections import GeneSetsCollection


@pytest.fixture(scope='session')
def autism_candidates_genes(request):
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_syms = gsc.get_gene_set('autism candidates from Iossifov PNAS 2015')
    return gene_syms['syms']
