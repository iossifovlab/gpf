import unittest

from query_prepare import prepare_gene_sets
import logging
from api.enrichment_query import enrichment_prepare
from hamcrest import *

logger = logging.getLogger(__name__)


class EnrichmentPrepareTests(unittest.TestCase):


    TEST_DATA_MAIN = {'denovoStudies': ['allWEAndTG'],
                      'transmittedStudies': ['w873e374s322'],
                      'geneSet': 'main',
                      'geneTerm': 'ChromatinModifiers'}

    def test_empty_denovo_study(self):
        data = enrichment_prepare({'denovoStudies': []})
        self.assertIsNone(data)

    def test_noneempty_result(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN)
        self.assertIsNotNone(data)

    def test_has_gene_set_main(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN)
        assert_that(data, has_key('geneSet'))
        assert_that(data, has_entry('geneSet', 'main'))

    def test_has_gene_term_main(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN)
        assert_that(data, has_key('geneTerm'))
        assert_that(data, has_entry('geneTerm', 'ChromatinModifiers'))
