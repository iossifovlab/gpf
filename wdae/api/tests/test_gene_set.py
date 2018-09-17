from builtins import str
import unittest
import logging
from DAE import giDB
from collections import defaultdict
import pytest
LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="no way of currently testing this")
class GeneSetTests(unittest.TestCase):
    def test_gene_terms_main(self):
        gene_terms = giDB.getGeneTerms('main')
        all_res = defaultdict(set)
        for gene_set_name in gene_terms.t2G:
            for gene_sym in gene_terms.t2G[gene_set_name]:
                for gsn in gene_terms.g2T[gene_sym]:
                    all_res[gsn].add(gene_sym)

        for gene_set_name in gene_terms.t2G:
            gene_set_syms = set(gene_terms.t2G[gene_set_name].keys())
            gene_set_syms1 = all_res[gene_set_name]
            res = gene_set_syms1.difference(gene_set_syms)
            LOGGER.debug("difference for %s: %s", gene_set_name, str(res))
            self.assertEquals(0, len(res))

    def test_gene_terms_main_reverse(self):
        # gene_terms = giDB.getGeneTerms('main')
        pass
