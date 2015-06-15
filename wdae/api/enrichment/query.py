'''
Created on Jun 12, 2015

@author: lubo
'''
from api.enrichment.results import EnrichmentTestBuilder


class EnrichmentQuery(object):
        
    def __init__(self, query, background):
        self.query = query
        self.background = background
        
    def build(self):
        self.enrichment_test = EnrichmentTestBuilder()
        self.enrichment_test.build(self.background)
        
    def calc(self):
        dsts = self.query['denovoStudies']
        gene_syms = self.query['geneSyms']
        self.result = self.enrichment_test.calc(dsts, gene_syms)
        
        return self.result
    
    