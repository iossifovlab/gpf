import unittest

# from query_prepare import prepare_gene_sets
import logging
from api.enrichment.enrichment_query import enrichment_prepare
from hamcrest import assert_that, has_entry, has_key, is_, none
from query_prepare import gene_set_bgloader
from denovo_gene_sets import build_denovo_gene_sets
from bg_loader import preload_background

logger = logging.getLogger(__name__)


class EnrichmentPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(EnrichmentPrepareTests, cls).setUpClass()

        builders = [
                (gene_set_bgloader,
                 ['GO'],
                 'GO'),

                (gene_set_bgloader,
                 ['MSigDB.curated'],
                 'MSigDB.curated'),

                (build_denovo_gene_sets,
                 [],
                 'Denovo'),
        ]
        
        preload_background(builders)
        
    def test_empty_denovo_study(self):
        data = enrichment_prepare({'denovoStudies': []})
        self.assertIsNone(data)

    TEST_DATA_MAIN = {'denovoStudies': ['IossifovWE2012'],
                      'transmittedStudies': ['w1202s766e611'],
                      'geneSet': 'main',
                      'geneTerm': 'ChromatinModifiers'}

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

    def test_has_gene_set_main_symbols(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN)
        assert_that(data, has_key('geneSyms'))

    TEST_DATA_BAD_GENE_SET = {'denovoStudies': ['IossifovWE2012'],
                              'transmittedStudies': ['w1202s766e611'],
                              'geneSet': 'BAD_GENE_SET',
                              'geneTerm': 'ChromatinModifiers'}

    def test_gene_set_bad(self):
        data = enrichment_prepare(self.TEST_DATA_BAD_GENE_SET)
        assert_that(data, is_(none()))

    TEST_DATA_BAD_GENE_TERM = {'denovoStudies': ['IossifovWE2012'],
                               'transmittedStudies': ['w1202s766e611'],
                               'geneSet': 'main',
                               'geneTerm': 'BAD_GENE_TERM'}

    def test_gene_term_bad(self):
        data = enrichment_prepare(self.TEST_DATA_BAD_GENE_TERM)
        assert_that(data, is_(none()))

    TEST_DATA_GENE_SYMS = {'denovoStudies': ['IossifovWE2012'],
                           'transmittedStudies': ['w1202s766e611'],
                           'geneSyms': ['POGZ']}

    def test_gene_syms(self):
        data = enrichment_prepare(self.TEST_DATA_GENE_SYMS)

        assert_that(data, has_key('geneSyms'))

    TEST_DATA_DENOVO_GENE_SET_NO_GENE_STUDY = \
        {'denovoStudies': ['IossifovWE2012'],
         'transmittedStudies': ['w1202s766e611'],
         'geneSet': 'denovo',
         'geneTerm': 'prb.LoF'}

    def test_denovo_gene_set_no_gene_study(self):
        data = enrichment_prepare(self.TEST_DATA_DENOVO_GENE_SET_NO_GENE_STUDY)

        assert_that(data, is_(none()))

    TEST_DATA_DENOVO_GENE_SET = \
        {'denovoStudies': ['IossifovWE2012'],
         'transmittedStudies': ['w1202s766e611'],
         'geneSet': 'denovo',
         'geneTerm': 'LoF',
         'gene_set_phenotype': 'autism'}

    def test_denovo_gene_set(self):
        data = enrichment_prepare(self.TEST_DATA_DENOVO_GENE_SET)

        assert_that(data, has_entry('gene_set_phenotype', 'autism'))
        assert_that(data, has_entry('geneSet', 'denovo'))
        assert_that(data, has_entry('geneTerm', 'LoF'))
        assert_that(data, has_key('geneSyms'))

    TEST_DATA_MAIN_BAD_DENOVO_STUDY = {'denovoStudies': ['BAD_STUDY'],
                                       'transmittedStudies': ['w1202s766e611'],
                                       'geneSet': 'main',
                                       'geneTerm': 'ChromatinModifiers'}

    def test_bad_denovo_study(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN_BAD_DENOVO_STUDY)
        assert_that(data, is_(none()))

    TEST_DATA_MAIN_BAD_TRANSMITTED_STUDY = {'denovoStudies': ['DalyWE2012'],
                                            'transmittedStudies': ['BAD_STUDY'],
                                            'geneSet': 'main',
                                            'geneTerm': 'ChromatinModifiers'}

    def test_bad_transmitted_study(self):
        data = enrichment_prepare(self.TEST_DATA_MAIN_BAD_TRANSMITTED_STUDY)
        assert_that(data, is_(none()))
