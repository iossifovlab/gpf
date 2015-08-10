'''
Created on May 27, 2015

@author: lubo
'''
import unittest

from denovo_gene_sets import set_genes, get_measure, \
    genes_sets, prb_set_per_phenotype, \
    get_all_denovo_studies,\
    build_prb_set_by_phenotype, build_sib_set, build_denovo_gene_sets
from DAE import vDB
from api.deprecated.bg_loader import preload_background, get_background

class Test(unittest.TestCase):


    def setUp(self):
        self.denovo_studies = vDB.get_studies("ALL WHOLE EXOME")

    def tearDown(self):
        pass


    def test_set_genes(self):
        gs = set_genes("main:FMR1-targets")
        self.assertTrue(gs)
        self.assertEquals(842, len(gs))

    def test_get_measure(self):
        nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')
        self.assertTrue(nvIQ)
        self.assertEqual(2757, len(nvIQ))
        
        
    def test_cnv_genes(self):
        cnv_studies = vDB.get_studies("LevyCNV2011")
        gene_set = genes_sets(cnv_studies,
                                      in_child="prb",
                                      effect_types="CNVs")
        
        self.assertTrue(len(gene_set) > 0)
        

    def test_apply_cnv_recurrent_test(self):
        all_tests = prb_set_per_phenotype()
        cnv_test = all_tests['CNV.Recurrent']
        cnv_studies = vDB.get_studies("LevyCNV2011")
        cnv_genes = cnv_test(cnv_studies)
        self.assertEquals(77, len(cnv_genes))
        
                
    def test_get_all_denovo_studies(self):
        all_denovo_studies = get_all_denovo_studies()
        self.assertEquals(10, len(all_denovo_studies))
        
    def test_build_prb_test_by_phenotype(self):
        all_denovo_studies = get_all_denovo_studies()
        
        gene_terms = build_prb_set_by_phenotype(all_denovo_studies, 'autism')
        self.assertTrue(gene_terms)
    
    def test_clean_prb_tests_by_phenotype(self):
        all_denovo_studies = get_all_denovo_studies()
        
        for phenotype in ['autism', 
                          'congenital heart disease', 
                          "epilepsy", 
                          'intelectual disability', 
                          'schizophrenia']:
            gene_terms = build_prb_set_by_phenotype(all_denovo_studies,
                                                    phenotype)
            for _key, value in gene_terms.t2G.items():
                self.assertTrue(len(value)>0)
                
    def test_build_sib_tests(self):
        denovo_studies = get_all_denovo_studies()
        gene_terms = build_sib_set(denovo_studies)
        
        for _key, value in gene_terms.t2G.items():
            self.assertTrue(len(value)>0)

    def test_build_denovo_gene_sets(self):
        res = build_denovo_gene_sets()
        self.assertIn('autism', res)
        self.assertIn('congenital heart disease', res)
        self.assertIn('epilepsy', res)
        self.assertIn('intelectual disability', res)
        self.assertIn('schizophrenia', res)
        self.assertIn('unaffected', res)
        
        
    def test_preload_denovo_gene_sets(self):
        builders = [(build_denovo_gene_sets,
                     [],
                     'Denovo')]
        
        preload_background(builders)
        
        gs = get_background('Denovo')
        self.assertTrue(gs)
        