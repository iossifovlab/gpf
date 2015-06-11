'''
Created on Jun 10, 2015

@author: lubo
'''
from api.enrichment import background
from api.enrichment.denovo_counters import DenovoEventsCounter,\
    DenovoRecurrentGenesCounter
from scipy import stats


class EnrichmentResult:
    def __init__(self, spec):
        self.spec = spec
        self.count = 0
        self.p_val = 0.0
        self.expected = 0.0

    def __str__(self):
        return "ET(%d (%0.4f), p_val=%f)" % \
            (self.count, self.expected, self.p_val)

    def __repr__(self):
        return self.__str__()
    
    
class EnrichmentTest(object):
    SYNONYMOUS_BACKGROUND = background.SynonymousBackground()
    
    def __init__(self, spec):
        self.spec = spec
        self.background = None
        self.counter = None

    @classmethod
    def make_variant_events_enrichment(cls, spec, background=SYNONYMOUS_BACKGROUND):
        res = cls(spec)
        res.background = background
        if not res.background.is_ready:
            res.background.precompute()
        res.counter = DenovoEventsCounter(spec)
        return res
    
    @classmethod
    def make_recurrent_genes_enrichment(cls, spec, background=SYNONYMOUS_BACKGROUND):
        res = cls(spec)
        res.background = background
        if not res.background.is_ready:
            res.background.precompute()
        res.counter = DenovoRecurrentGenesCounter(spec)
        return res
        
    def build(self, dsts, gene_syms):
        counter = self.counter.count(dsts, gene_syms)
        bg_prob = self.background.prob(gene_syms)
        
        res = EnrichmentResult(self.spec)
        res.count = counter.count
        res.total = counter.total
        res.expected = round(bg_prob * res.total, 4)
        res.p_val = stats.binom_test(res.count, res.total, p=bg_prob)
        
        return res
    
class EnrichmentTestBuilder(object):
    pass