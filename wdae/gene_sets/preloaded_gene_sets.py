'''
Created on Feb 29, 2016

@author: lubo
'''
from gene.gene_set_collections import GeneSetsCollections
import preloaded


class GeneSetsCollectionsPreload(preloaded.register.Preload):

    def __init__(self):
        self.gscs = None

    def is_loaded(self):
        return self.gscs

    def load(self):
        self.gscs = GeneSetsCollections()
        self.gscs.get_gene_sets_collections()

    def get(self):
        return self.gscs
