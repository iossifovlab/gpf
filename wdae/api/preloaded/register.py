'''
Created on Nov 5, 2015

@author: lubo
'''
from DAE import get_gene_sets_symNS


class Preload(object):

    def load(self):
        raise NotImplemented

    def get(self):
        raise NotImplemented


class GeneSetPreload(Preload):

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


_REGISTER = {}


def get_register():
    global _REGISTER
    return _REGISTER


def register(key, preload):
    global _REGISTER
    _REGISTER[key] = preload


def get(key):
    global _REGISTER

    try:
        value = _REGISTER.get(key)
    finally:
        pass

    return value


def has_key(key):
    global _REGISTER
    value = False

    try:
        value = _REGISTER.has_key(key)  # @IgnorePep8
    finally:
        pass

    return value
