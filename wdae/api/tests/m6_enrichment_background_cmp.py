'''
Created on Jun 10, 2015

@author: lubo
'''
import unittest
from DAE import vDB, get_gene_sets_symNS
from api.enrichment import background
from api.enrichment.enrichment import count_background,\
    build_transmitted_background
from api.query.query_prepare import prepare_transmitted_studies
from bg_loader import preload_background


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
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')
        self.gene_term = get_gene_sets_symNS('main')
        
        self.gene_syms = self.gene_term.t2G['FMR1-targets-1006genes'].keys()


    def tearDown(self):
        pass


    def test_build_background_single(self):
        countnew = self.background.count(self.gene_syms)
        
        count = count_background(self.gene_syms)
        self.assertEqual(count.cnt, countnew)
        
    def test_all_main(self):
        for gene_set in self.gene_term.t2G.keys():
            gene_syms = self.gene_term.t2G[gene_set].keys()
            
            countnew = self.background.count(gene_syms)
            count = count_background(gene_syms)
            
            self.assertEquals(count.cnt, countnew)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_build_background_and_compare']
    unittest.main()