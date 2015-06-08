import unittest
import logging

from api.enrichment.enrichment import enrichment_test, \
    build_transmitted_background

from DAE import vDB, get_gene_sets_symNS

logger = logging.getLogger(__name__)

import api.tests.enrichment_test_orig
from bg_loader import preload_background


class EnrichmentHelpersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsts = vDB.get_studies('ALL WHOLE EXOME')
        cls.tsts = vDB.get_study('w1202s766e611')
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
                    logger.error("wrong count numbers: %s != %s for %s:%s",
                                 str(o.cnt), str(r.cnt),
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                if o.pVal != r.p_val:
                    logger.error("wrong pVal: %s != %s for %s:%s",
                                 str(o.pVal), str(r.p_val),
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                if o.expected != r.expected:
                    logger.error("wrong expected: %s != %s for %s:%s",
                                 str(o.expected), str(r.expected),
                                 test_name,
                                 gene_set_name)
                    fail = True
                else:
                    print '.',

                r = totals[test_name][0]
                o = totals_orig[test_name]
                if o != r:
                    logger.error("wrong totals numbers: %s != %s for %s",
                                 str(o), str(r),
                                 test_name)
                    fail = True
                else:
                    print('.')

        self.assertFalse(fail, "wrong enrichment values detected...")
