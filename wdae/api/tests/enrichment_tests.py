import unittest
import logging

from api.enrichment import init_gene_set_symbols, build_variants_genes_dict, \
    init_gene_set_enrichment_full, count_gene_set_enrichment_full, \
    enrichment_test_full

from DAE import giDB, vDB

logger = logging.getLogger(__name__)

import api.tests.enrichment_test_orig


class EnrichmentHelpersTests(unittest.TestCase):

    # def test_init_gene_set_symbols(self):
    #     gene_terms = giDB.getGeneTerms('main')
    #     (gene_set_name, gene_set_symbols) = \
    #         init_gene_set_symbols(gene_terms, 'E15-maternal')
    #     self.assertEquals('E15-maternal', gene_set_name)
    #     logger.debug("gene set symbols: %s", str(gene_set_symbols))

    # def test_build_variants_genes_dict(self):
    #     dsts = vDB.get_studies('allWE')
    #     tsts = vDB.get_study('w873e374s322')
    #     var_genes_dict = build_variants_genes_dict(dsts, tsts)
    #     gene_terms = giDB.getGeneTerms('main')
    #     # logger.debug("variants to genes dict: %s", var_genes_dict)
    #     all_res = init_gene_set_enrichment_full(var_genes_dict, gene_terms)
    #     count_gene_set_enrichment_full(all_res, var_genes_dict, gene_terms)

    def test_count_variants_enrichment_E15_material(self):
        dsts = vDB.get_studies('allWE')
        tsts = vDB.get_study('w873e374s322')
        var_genes_dict = build_variants_genes_dict(dsts, tsts)
        gene_terms = giDB.getGeneTerms('main')
        # logger.debug("variants to genes dict: %s", var_genes_dict)
        all_res = init_gene_set_enrichment_full(var_genes_dict, gene_terms)
        count_gene_set_enrichment_full(all_res, var_genes_dict, gene_terms)

        res = all_res['E15-maternal']
        self.assertEqual(2893, res['BACKGROUND'].cnt)
        self.assertEqual(2, res['De novo prbFemaleLGDs'].cnt)
        self.assertEqual(6, res['De novo prbFemaleMissense'].cnt)
        self.assertEqual(8, res['De novo prbLGDs'].cnt)
        self.assertEqual(6, res['De novo prbMaleLGDs'].cnt)
        self.assertEqual(20, res['De novo prbMaleMissense'].cnt)
        self.assertEqual(26, res['De novo prbMissense'].cnt)
        self.assertEqual(7, res['De novo prbSynonymous'].cnt)
        self.assertEqual(1, res['De novo recPrbLGDs'].cnt)
        self.assertEqual(2, res['De novo sibFemaleLGDs'].cnt)
        self.assertEqual(3, res['De novo sibLGDs'].cnt)
        self.assertEqual(1, res['De novo sibMaleLGDs'].cnt)
        self.assertEqual(17, res['De novo sibMissense'].cnt)
        self.assertEqual(2, res['De novo sibSynonymous'].cnt)

    def test_count_variants_original(self):
        dsts = vDB.get_studies('allWE')
        tsts = vDB.get_study('w873e374s322')
        var_genes_dict = build_variants_genes_dict(dsts, tsts)
        gene_terms = giDB.getGeneTerms('main')

        original = api.tests.enrichment_test_orig.main(dsts, tsts, gene_terms)
        all_res_orig = original[1]
        # logger.debug("variants to genes dict: %s", var_genes_dict)
        all_res = init_gene_set_enrichment_full(var_genes_dict, gene_terms)
        count_gene_set_enrichment_full(all_res, var_genes_dict, gene_terms)

        fail = False
        for gene_set_name in all_res:
            res = all_res[gene_set_name]
            for test_name in res:
                if all_res_orig[gene_set_name][test_name].cnt != \
                   res[test_name].cnt:
                    logger.debug("wrong count numbers: %d != %d for %s:%s",
                                 all_res_orig[gene_set_name][test_name].cnt,
                                 res[test_name].cnt,
                                 test_name,
                                 gene_set_name)
                    fail = True
        self.assertFalse(fail, "wrong count found...")

    def test_enrichment_test_original(self):
        dsts = vDB.get_studies('allWE')
        tsts = vDB.get_study('w873e374s322')
        var_genes_dict = build_variants_genes_dict(dsts, tsts)
        gene_terms = giDB.getGeneTerms('main')

        original = api.tests.enrichment_test_orig.main(dsts, tsts, gene_terms)
        all_res_orig = original[1]

        all_res, totals = enrichment_test_full(var_genes_dict, gene_terms)
        fail = False

        for gene_set_name in all_res:
            res = all_res[gene_set_name]
            for test_name in res:
                r = res[test_name]
                o = all_res_orig[gene_set_name][test_name]
                if o.cnt != r.cnt:
                    logger.debug("wrong count numbers: %d != %d for %s:%s",
                                 o.cnt, r.cnt,
                                 test_name,
                                 gene_set_name)
                    fail = True
                if o.pVal != r.p_val:
                    logger.debug("wrong pVal: %f != %f for %s:%s",
                                 o.pVal, r.p_val,
                                 test_name,
                                 gene_set_name)
                    fail = True

                if o.expected != r.expected:
                    logger.debug("wrong expected: %d != %d for %s:%s",
                                 o.expected, r.expected,
                                 test_name,
                                 gene_set_name)
                    fail = True

        self.assertFalse(fail, "wrong enrichment values detected...")

        totals_orig = original[2]

        for test_name in totals:
            r = totals[test_name]
            o = totals_orig[test_name]
            if o != r:
                logger.debug("wrong totals numbers: %d != %d for %s",
                             o, r,
                             test_name)
                fail = True
        self.assertFalse(fail, "wrong totals detected...")
