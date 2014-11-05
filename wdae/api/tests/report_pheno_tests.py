import unittest

from api.report_pheno import pheno_prepare, pheno_query_variants
from query_prepare import prepare_denovo_studies

class PhenoTest(unittest.TestCase):
    TEST_DATA = {"denovoStudies": "combSSCWE",
                 "geneSet": "main",
                 "geneTerm": "essentialGenes",
                 "geneSyms": "",
                 'effectTypes': 'LGDs'}

    def test_just_test(self):
        res = pheno_prepare(self.TEST_DATA)
        self.assertTrue(res)

    def test_variants(self):
        vs = pheno_query_variants(self.TEST_DATA)
        self.assertTrue(vs)

    def test_studies(self):
        stds = prepare_denovo_studies(self.TEST_DATA)
        print(stds)
        self.assertTrue(stds)