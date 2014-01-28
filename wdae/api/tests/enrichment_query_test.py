import unittest

from query_prepare import prepare_gene_sets
import logging
from api.enrichment_query import enrichment_prepare


logger = logging.getLogger(__name__)



class EnrichmentPrepareTests(unittest.TestCase):

    def test_empty_denovo_study(self):
        data = enrichment_prepare({'denovoStudies': []})
        self.assertIsNone(data)
