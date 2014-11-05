import unittest

from api.report_pheno import pheno_query_variants, pheno_query
from query_prepare import prepare_denovo_studies

class PhenoTest(unittest.TestCase):
    TEST_DATA = {"denovoStudies": "cshlSSCWE",
                 'effectTypes': 'LGDs'}

    def test_variants(self):
        vs = pheno_query_variants(self.TEST_DATA)
        self.assertTrue(vs)

    def test_studies(self):
        stds = prepare_denovo_studies(self.TEST_DATA)
        print(stds)
        self.assertTrue(stds)

    def test_pheno_query(self):
        (all_families, families_with_hit) = pheno_query(self.TEST_DATA)
        self.assertTrue(all_families)
        self.assertTrue(families_with_hit)
        print(all_families)
        print(families_with_hit)