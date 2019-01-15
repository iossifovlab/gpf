'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
import pytest

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def test_denovo_gene_sets_exist(gscs):
    denovo = gscs.get_gene_sets_collection('denovo')
    assert denovo is not None


def test_get_all_gene_sets(gscs):
    gene_sets_collections = gscs.get_collections_descriptions()
    assert len(gene_sets_collections) != 0
