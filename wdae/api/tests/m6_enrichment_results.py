'''
Created on Jun 10, 2015

@author: lubo
'''
import unittest
from api.enrichment.results import EnrichmentTest
from api.enrichment.denovo_counters import filter_denovo_studies_by_phenotype
from DAE import vDB, get_gene_sets_symNS
from api.enrichment.config import PRB_TESTS_SPECS


class Test(unittest.TestCase):


    def setUp(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')
        gt = get_gene_sets_symNS('main')
        self.gene_syms = gt.t2G['FMR1-targets-1006genes'].keys()

    def tearDown(self):
        pass


    def test_autism_enrichment_result(self):
        spec = PRB_TESTS_SPECS[1]
        eres = EnrichmentTest.make_variant_events_enrichment(spec)
        adsts = filter_denovo_studies_by_phenotype(self.dsts, 'autism')
        res = eres.build(adsts, self.gene_syms)
        print res
        self.assertTrue(res)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_autism_enrichment_result']
    unittest.main()