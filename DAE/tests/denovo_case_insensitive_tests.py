'''
Created on Nov 10, 2015

@author: lubo
'''
import unittest
from DAE import vDB


class Test(unittest.TestCase):

    def setUp(self):
        self.study_name = "IossifovWE2014"
        self.study = vDB.get_study(self.study_name)

    def tearDown(self):
        pass

    def test_pogz_query(self):
        vs = self.study.get_denovo_variants(geneSyms=['POGZ'])
        count = 0
        for _v in vs:
            count += 1
        self.assertEqual(6, count)

    def test_pogz_query_case_insensitive(self):
        vs = self.study.get_denovo_variants(geneSyms=['pogz'])
        count = 0
        for _v in vs:
            count += 1
        self.assertEqual(6, count)


if __name__ == "__main__":
    unittest.main()
