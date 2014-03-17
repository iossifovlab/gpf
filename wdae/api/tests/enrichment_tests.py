import unittest
import logging

from api.enrichment import enrichment_test, build_transmitted_background

from DAE import vDB, get_gene_sets_symNS

logger = logging.getLogger(__name__)

import api.tests.enrichment_test_orig
from api.bg_loader import preload_background


class EnrichmentHelpersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsts = vDB.get_studies('allWE')
        cls.tsts = vDB.get_study('w873e374s322')
        cls.gene_terms = get_gene_sets_symNS('main')
        logger.debug("calculating original enrichment test values...")
        cls.original = api.tests.enrichment_test_orig.main(cls.dsts,
                                                           cls.tsts,
                                                           cls.gene_terms)
        builders = [(build_transmitted_background,
                     [cls.tsts],
                     'enrichment_background')]

        preload_background(builders)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_enrichment_full_count_original(self):
        all_res_orig = self.original[1]
        totals_orig = self.original[2]
        fail = False
        for gene_set_name in all_res_orig:

            logger.debug("calculating new enrichment test values...")
            gene_syms_set = set(self.gene_terms.t2G[gene_set_name].keys())

            res, totals = enrichment_test(self.dsts,
                                          gene_syms_set)

            for test_name in res:
                r = res[test_name]
                o = all_res_orig[gene_set_name][test_name]
                if o.cnt != r.cnt:
                    logger.debug("wrong count numbers: %d != %d for %s:%s",
                                 o.cnt, r.cnt,
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                if o.pVal != r.p_val:
                    logger.debug("wrong pVal: %f != %f for %s:%s",
                                 o.pVal, r.p_val,
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                if o.expected != r.expected:
                    logger.debug("wrong expected: %d != %d for %s:%s",
                                 o.expected, r.expected,
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                r = totals[test_name]
                o = totals_orig[test_name]
                if o != r:
                    logger.debug("wrong totals numbers: %d != %d for %s",
                                 o, r,
                                 test_name)
                    fail = True
        self.assertFalse(fail, "wrong enrichment values detected...")
