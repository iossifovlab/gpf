'''
Created on Feb 29, 2016

@author: lubo
'''
from __future__ import unicode_literals
from gene.gene_set_collections import GeneSetsCollections
import preloaded.register


class GeneSetsCollectionsPreload(preloaded.register.Preload):

    def __init__(self):
        self.gscs = None

    def is_loaded(self):
        return self.gscs

    def load(self):
        self.gscs = GeneSetsCollections()

    def get(self):
        return self.gscs
