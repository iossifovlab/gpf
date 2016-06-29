'''
Created on Jun 29, 2016

@author: lubo
'''
import unittest
from pheno_families.pheno_filter import PhenoMeasureFilters


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.pheno_filters = PhenoMeasureFilters()

    def test_get_matching_probands(self):
        probands = self.pheno_filters.get_matching_probands(
            "non_verbal_iq", 9, 10)
        print(probands)

        self.assertEquals(1, len(probands))

    def test_get_matching_siblings(self):
        siblings = self.pheno_filters.get_matching_siblings(
            "non_verbal_iq")
        self.assertEquals(0, len(siblings))
