import unittest
import logging
import itertools

from query_prepare import prepare_denovo_studies
from query_variants import dae_query_variants

from api.enrichment import collect_prb_enrichment_variants_by_phenotype, \
    collect_sib_enrichment_variants_by_phenotype, \
    filter_prb_enrichment_variants_by_phenotype, \
    filter_sib_enrichment_variants_by_phenotype

logger = logging.getLogger(__name__)


class EnrichmentBasicTest(unittest.TestCase):
    def test_collect_prb_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }
        
        dsts = prepare_denovo_studies(data)
        res = collect_prb_enrichment_variants_by_phenotype(dsts)

        logger.info("collected variants: %s", res)
        logger.info("collected variants phenotypes: %s", len(res.keys()))
        self.assertEqual(5, len(res.keys()))

    def test_collect_prb_variants_by_phenotype_autism(self):
        data = {
            "denovoStudies":"AUTISM",
        }
        
        dsts = prepare_denovo_studies(data)
        res = collect_prb_enrichment_variants_by_phenotype(dsts)

        logger.info("collected variants: %s", res)
        logger.info("collected variants phenotypes: %s", len(res.keys()))
        self.assertEqual(1, len(res.keys()))

    def test_collect_sib_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }
        
        dsts = prepare_denovo_studies(data)
        res = collect_sib_enrichment_variants_by_phenotype(dsts)

        logger.info("collected SIB variants: %s", res)
        self.assertEqual(5, len(res))

    def test_filter_prb_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }
        
        dsts = prepare_denovo_studies(data)
        evars = collect_prb_enrichment_variants_by_phenotype(dsts)

        res = filter_prb_enrichment_variants_by_phenotype(evars)
        logger.info("filtered enrichment variants phenotypes: %s", res.keys())
        self.assertEqual(5, len(res.keys()))
        for phenotype, fevars in res.items():
            self.assertEqual(8, len(fevars))

            
    def test_filter_prb_variants_by_phenotype_autism(self):
        data = {
            "denovoStudies":"AUTISM",
        }
        
        dsts = prepare_denovo_studies(data)
        evars = collect_prb_enrichment_variants_by_phenotype(dsts)

        res = filter_prb_enrichment_variants_by_phenotype(evars)
        logger.info("filtered enrichment variants phenotypes: %s", res.keys())
        self.assertEqual(1, len(res.keys()))

        for phenotype, fevars in res.items():
            self.assertEqual(8, len(fevars))

    def test_filter_sib_variants_by_phenotype_whole_exome(self):
        data = {
            "denovoStudies":"ALL WHOLE EXOME",
        }
        
        dsts = prepare_denovo_studies(data)
        evars = collect_sib_enrichment_variants_by_phenotype(dsts)
        res = filter_sib_enrichment_variants_by_phenotype(evars)
        
        self.assertEqual(5, len(res))
