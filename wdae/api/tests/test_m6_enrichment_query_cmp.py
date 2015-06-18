'''
Created on Jun 12, 2015

@author: lubo
'''
import unittest
from api.enrichment import background
from api.query.query_prepare import prepare_transmitted_studies
from api.enrichment.enrichment import build_transmitted_background
from api.deprecated.bg_loader import preload_background
from api.enrichment.enrichment_query import enrichment_results_by_phenotype,\
    enrichment_prepare
from api.enrichment.results import EnrichmentTestBuilder
from api.enrichment.views import EnrichmentView

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

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.background = background.SynonymousBackground()
        cls.background.precompute()
        
        transmitted = prepare_transmitted_studies(
            {"transmittedStudies": 'w1202s766e611'})

        builders = [
            (build_transmitted_background,
             transmitted,
             'enrichment_background')
        ]
        
        preload_background(builders)
        
                
    def setUp(self):
        pass


    def tearDown(self):
        pass

    FULL_QUERY = {'denovoStudies': 'ALL WHOLE EXOME',
                  'geneSet':'main',
                  'geneTerm': 'FMR1-targets-1006genes'}
    
#     def test_full_query(self):
#         
#         data = EnrichmentView.enrichment_prepare(self.FULL_QUERY)
#         enrichment_query = EnrichmentQuery(data, self.background)
#         enrichment_query.build()
#         
#         _res = enrichment_query.calc()
            
    def test_all_query(self):
        data = EnrichmentView.enrichment_prepare(self.FULL_QUERY)
        enrichment_query = EnrichmentQuery(data, self.background)

        enrichment_query.build()
        
        res = enrichment_query.calc()

        res_old = enrichment_results_by_phenotype(
                **enrichment_prepare(self.FULL_QUERY))
        
        for phenotype in res.keys():
            er = res[phenotype]
            er_old = res_old[phenotype]
            for r, r_old in zip(er, er_old):
                
                self.assertEquals(r.count, r_old['count'])
                self.assertAlmostEquals(r.expected, float(r_old['expected']),
                                        places=4)
                self.assertAlmostEquals(r.p_val, float(r_old['p_val']),
                                        places=4)
                self.assertEquals(r.total, r_old['overlap'])
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()