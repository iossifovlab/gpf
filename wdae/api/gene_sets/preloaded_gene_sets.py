'''
Created on Feb 29, 2016

@author: lubo
'''
import preloaded
from DAE import get_gene_sets_symNS


class GeneSetPreload(preloaded.register.Preload):

    def __init__(self, name):
        self.name = name

    def load(self):
        self.gene_term = get_gene_sets_symNS(self.name)

    def get(self):
        return self.gene_term


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
