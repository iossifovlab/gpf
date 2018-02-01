'''
Created on Feb 29, 2016

@author: lubo
'''
import cPickle
import zlib

from gene.gene_set_collections import GeneSetsCollection, DenovoGeneSetsCollection
import precompute
import preloaded


# from DAE import get_gene_sets_symNS
class GeneSetPreload(preloaded.register.Preload):

    def __init__(self, name):
        self.name = name
        self.gsc = None

    def is_loaded(self):
        return self.gsc

    def load(self):
        self.gsc = GeneSetsCollection(self.name)
        self.gsc.load()

    def get(self):
        return self.gsc


class GoTermsPreload(GeneSetPreload):

    def __init__(self):
        super(GoTermsPreload, self).__init__('GO')


class MainPreload(GeneSetPreload):

    def __init__(self):
        super(MainPreload, self).__init__('main')


class MSigDBPreload(GeneSetPreload):

    def __init__(self):
        super(MSigDBPreload, self).__init__('MSigDB.curated')


class ProteinDomainsPreload(GeneSetPreload):

    def __init__(self):
        super(ProteinDomainsPreload, self).__init__('domain')


class MiRNADarnellDomainsPreload(GeneSetPreload):

    def __init__(self):
        super(MiRNADarnellDomainsPreload, self).__init__('miRNA.Darnell')


class DenovoGeneSetsPreload(GeneSetPreload):

    def __init__(self):
        super(DenovoGeneSetsPreload, self).__init__('denovo')

    def load(self):
        self.gsc = DenovoGeneSetsCollection()
        self.gsc.load()
