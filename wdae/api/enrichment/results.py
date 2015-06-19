'''
Created on Jun 10, 2015

@author: lubo
'''
from api.enrichment import background
from api.enrichment.denovo_counters import DenovoEventsCounter,\
    DenovoRecurrentGenesCounter, filter_denovo_studies_by_phenotype
from scipy import stats
from api.enrichment.config import PHENOTYPES, PRB_TESTS_SPECS, SIB_TESTS_SPECS


class EnrichmentTest(object):

    def __init__(self, spec):
        self.spec = spec
        self.background = None
        self.counter = None

    @classmethod
    def make_variant_events_enrichment(cls, spec):
        res = cls(spec)
        res.background = background
        if not res.background.is_ready:
            res.background.precompute()
        res.counter = DenovoEventsCounter(spec)
        return res
    
    @classmethod
    def make_recurrent_genes_enrichment(cls, spec):
        res = cls(spec)
        res.background = background
        if not res.background.is_ready:
            res.background.precompute()
        res.counter = DenovoRecurrentGenesCounter(spec)
        return res
        
    def calc(self, dsts, gene_syms):
        res = self.counter.count(dsts, gene_syms)
        bg_prob = self.background.prob(gene_syms)
        
        res.expected = round(bg_prob * res.total, 4)
        res.p_val = stats.binom_test(res.count, res.total, p=bg_prob)

        return res
    
class EnrichmentTestBuilder(object):
    
    def _build_test(self, background, spec):
        spec_type = spec['type']
        if spec_type == 'event':
            test = EnrichmentTest.make_variant_events_enrichment(spec, background)
        elif spec_type == 'rec':
            test = EnrichmentTest.make_recurrent_genes_enrichment(spec, background)
        else:
            raise ValueError("bad enrichment test type {}".format(spec_type))
        return test

    def _prb_build(self, background):
        self.prb_tests = []
        for spec in PRB_TESTS_SPECS:
            test = self._build_test(background, spec)
            self.prb_tests.append(test)
            
        return self.prb_tests
    
    def _sib_build(self, background):
        self.sib_sets = []
        for spec in SIB_TESTS_SPECS:
            test = self._build_test(background, spec)
            self.sib_sets.append(test)
        
        return self.sib_sets
    
    def _prb_calc(self, dsts, gene_syms):
        res = []
        for test in self.prb_tests:
            r = test.calc(dsts, gene_syms)
            res.append(r)
        return res
    
    def _sib_calc(self, dsts, gene_syms):
        res = []
        for test in self.sib_sets:
            r = test.calc(dsts, gene_syms)
            res.append(r)
        return res
    
    def build(self, background):
        self._prb_build(background)
        self._sib_build(background)
        
    def _calc_by_phenotype(self, dsts, phenotype, gene_syms):
        if phenotype == 'unaffected':
            res = self._sib_calc(dsts, gene_syms)
            return ('unaffected', res)

        pdsts = filter_denovo_studies_by_phenotype(dsts, phenotype)
        if not pdsts:
            return None
        
        res = self._prb_calc(pdsts, gene_syms)
        return (phenotype, res)
    
    def calc(self, dsts, gene_syms):
        res = {}
        for phenotype in PHENOTYPES:
            (ph, er) = self._calc_by_phenotype(
                    dsts,
                    phenotype, 
                    gene_syms)

            assert ph == phenotype
            
            res[phenotype] = er
        return res
    