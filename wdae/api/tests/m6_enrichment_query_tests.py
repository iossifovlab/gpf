'''
Created on Jun 12, 2015

@author: lubo
'''
import unittest
from api.enrichment import background
from api.enrichment.query import Query


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.background = background.SynonymousBackground()
        cls.background.precompute()
        
                
    def setUp(self):
        pass


    def tearDown(self):
        pass

    FULL_QUERY = {'denovoStudies': 'ALL WHOLE EXOME',
                  'geneSet':'main',
                  'geneTerm': 'FMR1-targets-1006genes'}
    
    def test_full_query(self):
        enrichment_query = Query.make_query(self.FULL_QUERY, self.background)
        enrichment_query.build()
        
        res = enrichment_query.calc()
        print(res)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()