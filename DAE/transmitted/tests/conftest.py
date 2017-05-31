'''
Created on May 22, 2017

@author: lubo
'''
import pytest
import DAE


@pytest.fixture(scope='session')
def autism_candidates_genes(request):
    gt = DAE.get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()
    return gene_syms
