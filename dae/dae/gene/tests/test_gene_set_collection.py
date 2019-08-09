'''
Created on Feb 24, 2017

@author: lubo
'''
from dae.gene.gene_set_collections import GeneSetsCollection


def test_gene_sets_collection_main(gene_info_config):
    gsc = GeneSetsCollection('main', config=gene_info_config)
    gsc.load()
