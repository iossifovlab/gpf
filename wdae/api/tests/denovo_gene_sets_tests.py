'''
Created on May 27, 2015

@author: lubo
'''
import unittest

from denovo_gene_sets import set_genes, get_measure, \
    genes_test, prb_tests_per_phenotype, \
    get_all_denovo_studies,\
    build_prb_test_by_phenotype, build_sib_test, build_denovo_gene_sets
from DAE import vDB

class Test(unittest.TestCase):


    def setUp(self):
        self.denovo_studies = vDB.get_studies("ALL WHOLE EXOME")

    def tearDown(self):
        pass


#     def test_get_denovo_sets_simple(self):
#         denovo_gene_sets = get_denovo_gene_sets_by_phenotype()
#         print(denovo_gene_sets.t2G.keys())
            

    def test_set_genes(self):
        gs = set_genes("main:FMR1-targets")
        self.assertTrue(gs)
        self.assertEquals(842, len(gs))

    def test_get_measure(self):
        nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')
        self.assertTrue(nvIQ)
        print(nvIQ)
        self.assertEqual(2757, len(nvIQ))
        
#     def test_get_denovo_studies_by_phenotype(self):
#         studies = get_denovo_studies_by_phenotype()
#         self.assertTrue(studies)
#         self.assertIn("autism", studies)
#         self.assertIn("epilepsy", studies)
#         self.assertIn("congenital heart disease", studies)
#         
#         self.assertTrue(studies['autism'])
#         self.assertTrue(studies['epilepsy'])
#         self.assertTrue(studies['congenital heart disease'])
# 
#     def test_prb_default_tests_by_phenotype(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         gene_sets = prb_default_tests_by_phenotype(all_studies)
#         # print(gene_sets)
#         self.assertTrue(gene_sets)
#         self.assertIn('schizophrenia', gene_sets)
#         schizo_gene_sets = gene_sets['schizophrenia']
#         self.assertIn('LoF', schizo_gene_sets)
#         self.assertIn('LoF.Male', schizo_gene_sets)
#         self.assertIn('LoF.Female', schizo_gene_sets)        
#         self.assertIn('Missense', schizo_gene_sets)
#         self.assertIn('Missense.Male', schizo_gene_sets)
#         self.assertIn('Missense.Female', schizo_gene_sets)
#         self.assertIn('Synonymous', schizo_gene_sets)
#         
#     def test_prb_measure_tests_by_phenotype(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         gene_sets = prb_default_tests_by_phenotype(all_studies)
#         # print(gene_sets)
#         self.assertTrue(gene_sets)
#         self.assertIn('autism', gene_sets)
#         autism_gene_sets = gene_sets['autism']
#         self.assertIn('LoF.LowIQ', autism_gene_sets)
#         self.assertIn('LoF.HighIQ', autism_gene_sets)
#           
#     def test_prb_cnv_tests_by_phenotype(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         gene_sets = prb_default_tests_by_phenotype(all_studies)
#         # print(gene_sets)
#         self.assertTrue(gene_sets)
#         self.assertIn('congenital heart disease', gene_sets)
#         congenital_heart_disease = gene_sets['congenital heart disease']
#         self.assertIn('CNV', congenital_heart_disease)
#         self.assertIn('Dup', congenital_heart_disease)
#         self.assertIn('Del', congenital_heart_disease)
#           
#     def test_prb_cnv_recurrent_tests_by_phenotype(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         gene_sets = prb_default_tests_by_phenotype(all_studies)
#         # print(gene_sets)
#         self.assertTrue(gene_sets)
#         self.assertIn('autism', gene_sets)
#         autism = gene_sets['autism']
#         self.assertIn('CNV', autism)
#         self.assertIn('Dup', autism)
#         self.assertIn('Del', autism)
#     
#         self.assertIn('CNV.Recurrent', autism)
#         
#     def test_studies_by_phenotype(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         for key, studies in all_studies.items():
#             if key=="all":
#                 continue
#             for study in studies:
#                 print(key, study.get_attr('study.phenotype'))
#                 self.assertEquals(key, study.get_attr('study.phenotype'))
#         
#         [cnv_study] = vDB.get_studies("LevyCNV2011")
#         self.assertIn(cnv_study, all_studies['autism'])
        
#         all_set = set()
#         for studies in all_studies.items():
#             print(studies)
#             all_set.union(set(studies))
#         self.assertEqual(11, len(all_set))
        
    def test_cnv_genes(self):
        cnv_studies = vDB.get_studies("LevyCNV2011")
        print(cnv_studies)
        gene_set = genes_test(cnv_studies,
                                      in_child="prb",
                                      effect_types="CNVs")
        
        self.assertTrue(len(gene_set) > 0)
        

    def test_apply_cnv_recurrent_test(self):
        all_tests = prb_tests_per_phenotype()
        cnv_test = all_tests['CNV.Recurrent']
        cnv_studies = vDB.get_studies("LevyCNV2011")
        cnv_genes = cnv_test(cnv_studies)
        self.assertEquals(77, len(cnv_genes))
        
#     def test_apply_cnv_tests_to_autism_studies(self):
#         all_studies = get_denovo_studies_by_phenotype()
#         autism_studies=all_studies['autism']
#         
#         all_tests = prb_tests_per_phenotype()
#         cnv_test = all_tests['CNV.Recurrent']
#         cnv_genes = cnv_test(autism_studies)
#         self.assertEquals(77, len(cnv_genes))
#         
#         cnv_test = all_tests['CNV']
#         cnv_genes = cnv_test(autism_studies)
#         self.assertEquals(818, len(cnv_genes))
#         
#         cnv_test = all_tests['Dup']
#         cnv_genes = cnv_test(autism_studies)
#         self.assertEquals(430, len(cnv_genes))
#     
#         cnv_test = all_tests['Del']
#         cnv_genes = cnv_test(autism_studies)
#         self.assertEquals(425, len(cnv_genes))
        
#     def test_siblings_tests(self):
#         all_studies = get_denovo_studies_by_phenotype()
# 
#         gene_sets = sib_default_tests(all_studies)
#         print(gene_sets)
#         
#         for key, gs in gene_sets.items():
#             print(key, gs)
#             self.assertTrue(len(gs)>0)
# 
# 
#     def test_clean_denovo_gene_sets(self):
#         gene_sets = get_denovo_gene_sets_by_phenotype()
#         
#         for gss in gene_sets.values():
#             for key, gs in gss.items():
#                 print(key, gs)
#                 self.assertTrue(len(gs)>0)
                
    def test_get_all_denovo_studies(self):
        all_denovo_studies = get_all_denovo_studies()
        self.assertEquals(11, len(all_denovo_studies))
        
    def test_build_prb_test_by_phenotype(self):
        all_denovo_studies = get_all_denovo_studies()
        
        gene_terms = build_prb_test_by_phenotype(all_denovo_studies, 'autism')
        self.assertTrue(gene_terms)
    
    def test_clean_prb_tests_by_phenotype(self):
        all_denovo_studies = get_all_denovo_studies()
        
        for phenotype in ['autism', 'congenital heart disease', "epilepsy", 'intelectual disability', 'schizophrenia']:
            gene_terms = build_prb_test_by_phenotype(all_denovo_studies, phenotype)
            for key, value in gene_terms.t2G.items():
                print("checking set: " + phenotype + '.' + key)
                self.assertTrue(len(value)>0)
                
    def test_build_sib_tests(self):
        denovo_studies = get_all_denovo_studies()
        gene_terms = build_sib_test(denovo_studies)
        
        for key, value in gene_terms.t2G.items():
            print("checking set: unaffected." + key)
            self.assertTrue(len(value)>0)

    def test_build_denovo_gene_sets(self):
        res = build_denovo_gene_sets()
        self.assertIn('autism', res)
        self.assertIn('congenital heart disease', res)
        self.assertIn('epilepsy', res)
        self.assertIn('intelectual disability', res)
        self.assertIn('schizophrenia', res)
        self.assertIn('unaffected', res)
        
        
        