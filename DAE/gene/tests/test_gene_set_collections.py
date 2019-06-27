'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
import pytest

pytestmark = pytest.mark.skip('depends on real data')


def test_gscs_config_cache(gscs):
    assert gscs.cache is not None


def test_gscs_get_gene_set_collection_main(gscs):
    assert gscs is not None
    main = gscs.get_gene_sets_collection('main')
    assert main is not None


def test_gscs_get_main_gene_sets(gscs):
    main_gene_sets = gscs.get_gene_sets('main')
    assert 15 == len(main_gene_sets)


def test_gscs_has_main_gene_sets_collection(gscs):
    assert gscs.has_gene_sets_collection('main')
