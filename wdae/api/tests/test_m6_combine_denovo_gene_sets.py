'''
Created on Jun 30, 2015

@author: lubo
'''
import unittest
from api.dae_query import load_gene_set2, combine_denovo_gene_sets,\
    gene_terms_union, collect_denovo_gene_sets


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_combine_denovo_gene_sets(self):
        gene_sets = combine_denovo_gene_sets('autism,unaffected')
        self.assertTrue(gene_sets)
    
    def test_union_denovo_gene_sets(self):
        gene_terms = collect_denovo_gene_sets('autism,unaffected')
        gene_term = gene_terms_union(gene_terms)
        
        self.assertTrue(gene_term)

    def test_single_pheno(self):
        gene_sets = load_gene_set2('denovo', 'autism')
        self.assertTrue(gene_sets)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_combine_denovo_gene_sets']
    unittest.main()