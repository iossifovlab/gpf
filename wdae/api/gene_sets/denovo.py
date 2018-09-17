'''
Created on Jun 15, 2015

@author: lubo
'''
from future import standard_library
standard_library.install_aliases()
import precompute
from denovo_gene_sets import build_denovo_gene_sets
import pickle
import zlib


class PrecomputeDenovoGeneSets(precompute.register.Precompute):
    def __init__(self):
        self.denovo_gene_sets = {}

    def precompute(self):
        self.denovo_gene_sets = build_denovo_gene_sets()

    def is_precomputed(self):
        return self.denovo_gene_sets

    def serialize(self):
        result = {}
        for key, gs in list(self.denovo_gene_sets.items()):
            data = zlib.compress(pickle.dumps(gs, protocol=2))
            result[key] = data

        return result

    def deserialize(self, data):
        self.denovo_gene_sets = {
            k: pickle.loads(zlib.decompress(d))
            for k, d in list(data.items())}
