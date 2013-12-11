import unittest
import logging

from api.enrichment import __init_gene_set_symbols
from DAE import giDB

logger = logging.getLogger(__name__)


class EnrichmentHelpersTests(unittest.TestCase):

    def test_init_gene_set_symbols(self):
        gene_terms = giDB.getGeneTerms('main')
        (gene_set_name, gene_set_symbols) = \
            __init_gene_set_symbols('E15-maternal', gene_terms)
        self.assertEquals('E15-maternal', gene_set_name)
        logger.debug("gene set symbols: ", str(gene_set_symbols))
