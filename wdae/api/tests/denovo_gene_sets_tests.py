'''
Created on May 27, 2015

@author: lubo
'''
import unittest

from query_denovo_gene_sets import get_denovo_sets, set_genes, get_measure, \
    get_denovo_studies_by_phenotype, prb_default_tests_by_phenotype
from DAE import vDB

class Test(unittest.TestCase):


    def setUp(self):
        self.denovo_studies = vDB.get_studies("ALL WHOLE EXOME")

    def tearDown(self):
        pass


    def test_get_denovo_sets_simple(self):
        denovo_gene_sets = get_denovo_sets(self.denovo_studies)
        print(denovo_gene_sets.t2G.keys())
            

    def test_set_genes(self):
        gs = set_genes("main:FMR1-targets")
        self.assertTrue(gs)
        self.assertEquals(842, len(gs))

    def test_get_measure(self):
        nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')
        self.assertTrue(nvIQ)
        print(nvIQ)
        self.assertEqual(2757, len(nvIQ))
        
    def test_get_denovo_studies_by_phenotype(self):
        studies = get_denovo_studies_by_phenotype()
        self.assertTrue(studies)
        self.assertIn("autism", studies)
        self.assertIn("epilepsy", studies)
        self.assertIn("congenital heart disease", studies)
        
        self.assertTrue(studies['autism'])
        self.assertTrue(studies['epilepsy'])
        self.assertTrue(studies['congenital heart disease'])

    def test_prb_default_tests_by_phenotype(self):
        all_studies = get_denovo_studies_by_phenotype()
        gene_sets = prb_default_tests_by_phenotype(all_studies)
        # print(gene_sets)
        self.assertTrue(gene_sets)
        self.assertIn('schizophrenia', gene_sets)
        schizo_gene_sets = gene_sets['schizophrenia']
        self.assertIn('LoF', schizo_gene_sets)
        self.assertIn('LoF.Male', schizo_gene_sets)
        self.assertIn('LoF.Female', schizo_gene_sets)        
        self.assertIn('Missense', schizo_gene_sets)
        self.assertIn('Missense.Male', schizo_gene_sets)
        self.assertIn('Missense.Female', schizo_gene_sets)
        self.assertIn('Synonymous', schizo_gene_sets)
        
    def test_prb_measure_tests_by_phenotype(self):
        all_studies = get_denovo_studies_by_phenotype()
        gene_sets = prb_default_tests_by_phenotype(all_studies)
        # print(gene_sets)
        self.assertTrue(gene_sets)
        self.assertIn('autism', gene_sets)
        autism_gene_sets = gene_sets['autism']
        self.assertIn('LoF.LowIQ', autism_gene_sets)
        self.assertIn('LoF.HighIQ', autism_gene_sets)
          
    def test_prb_cnv_tests_by_phenotype(self):
        all_studies = get_denovo_studies_by_phenotype()
        gene_sets = prb_default_tests_by_phenotype(all_studies)
        # print(gene_sets)
        self.assertTrue(gene_sets)
        self.assertIn('congenital heart disease', gene_sets)
        congenital_heart_disease = gene_sets['congenital heart disease']
        self.assertIn('CNV', congenital_heart_disease)
        self.assertIn('Dup', congenital_heart_disease)
        self.assertIn('Del', congenital_heart_disease)
          
    
        