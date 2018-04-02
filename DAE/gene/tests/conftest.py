'''
Created on Mar 29, 2018

@author: lubo
'''
import pytest
from gene.gene_set_collections import GeneSetsCollections


@pytest.fixture(scope='session')
def gscs():
    res = GeneSetsCollections()
    return res
