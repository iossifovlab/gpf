'''
Created on Jun 30, 2015

@author: lubo
'''

import unittest
from helpers.dae_query import combine_denovo_gene_sets,\
    gene_terms_union, collect_denovo_gene_sets
from helpers.GeneTerm import ddunion
from api.query.wdae_query_variants import gene_set_loader2


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
        gene_term = gene_set_loader2('denovo', 'autism')
        self.assertTrue(gene_term)

    def test_ddunion_t2g(self):
        gene_terms = collect_denovo_gene_sets('autism,unaffected')
        gt1 = gene_terms[0].t2G
        gt2 = gene_terms[1].t2G
        r = ddunion(gt1, gt2)
        self.assertTrue(r)
        for k in set(gt1.keys()).union(gt2.keys()):
            self.assertIn(k, r)
            if k in gt1 and k in gt2:
                v1 = gt1[k]
                v2 = gt2[k]
                rv = r[k]
                for rk in set(v1.keys()).union(v2.keys()):
                    self.assertIn(rk, rv)

    def test_ddunion_g2t(self):
        gene_terms = collect_denovo_gene_sets('autism,unaffected')
        gt1 = gene_terms[0].g2T
        gt2 = gene_terms[1].g2T
        r = ddunion(gt1, gt2)
        self.assertTrue(r)
        for k in set(gt1.keys()).union(gt2.keys()):
            self.assertIn(k, r)
            if k in gt1 and k in gt2:
                v1 = gt1[k]
                v2 = gt2[k]
                rv = r[k]
                for rk in set(v1.keys()).union(v2.keys()):
                    self.assertIn(rk, rv)

    def test_double_pheno(self):
        gene_term = gene_set_loader2('denovo', 'autism,unaffected')
        self.assertTrue(gene_term)

    def test_double_pheno_lgds_gene_syms(self):
        gene_syms = set()
        for gt in collect_denovo_gene_sets('autism,unaffected'):
            gs = set(gt.t2G['LGDs.Recurrent'].keys())
            gene_syms = gene_syms.union(gs)
        gene_term = gene_set_loader2('denovo', 'autism,unaffected')
        gene_syms2 = set(gene_term.t2G['LGDs.Recurrent'].keys())
        self.assertEquals(gene_syms, gene_syms2)


if __name__ == "__main__":
    unittest.main()
