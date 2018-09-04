'''
Created on Feb 27, 2017

@author: lubo
'''
import pytest


def test_load_cache(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    computed = denovo.load()
    assert computed is not None
