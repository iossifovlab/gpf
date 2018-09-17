'''
Created on Feb 27, 2017

@author: lubo
'''
from __future__ import unicode_literals
import pytest
from gene.gene_set_collections import GeneSetsCollections


@pytest.fixture(scope='session')
def gscs(request):
    res = GeneSetsCollections()
    return res


def test_load_cache(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    computed = denovo.load()
    assert computed is not None
