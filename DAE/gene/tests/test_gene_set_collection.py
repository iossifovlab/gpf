'''
Created on Feb 24, 2017

@author: lubo
'''
from __future__ import unicode_literals
from gene.gene_set_collections import GeneSetsCollection


def test_gene_sets_collection_main():
    gsc = GeneSetsCollection('main')
    gsc.load()
