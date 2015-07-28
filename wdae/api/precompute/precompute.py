'''
Created on Jun 15, 2015

@author: lubo
'''
from api.precompute.register import Precompute
from denovo_gene_sets import build_denovo_gene_sets
import cPickle
import zlib


class PrecomputeDenovoGeneSets(Precompute):
    def __init__(self):
        self.denovo_gene_sets = {}

    def precompute(self):
        self.denovo_gene_sets = build_denovo_gene_sets()

    def serialize(self):
        result = {}
        for key, gs in self.denovo_gene_sets.items():
            data = zlib.compress(cPickle.dumps(gs))
            result[key] = data

        return result

    def deserialize(self, data):
        self.denovo_gene_sets = {
            k: cPickle.loads(zlib.decompress(d))
            for k, d in data.items()}
