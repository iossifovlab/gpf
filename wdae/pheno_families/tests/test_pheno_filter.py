'''
Created on Jun 29, 2016

@author: lubo
'''
import unittest
from pheno_families.pheno_filter import PhenoMeasureFilters, PhenoStudyFilter


class PhenoMeasureFiltersTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.pheno_filters = PhenoMeasureFilters()

    def test_get_matching_probands(self):
        probands = self.pheno_filters.get_matching_probands(
            "non_verbal_iq", 9, 10)

        self.assertEquals(1, len(probands))

    def test_get_matching_siblings(self):
        siblings = self.pheno_filters.get_matching_siblings(
            "non_verbal_iq")
        self.assertEquals(0, len(siblings))


class PhenoStudyFilterTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.study_filters = PhenoStudyFilter()

    def test_study_types(self):
        types = self.study_filters._build_study_types()
        self.assertEquals(set(["WE", "TG", "CNV"]),
                          set(types))

    def test_get_matching_probands_by_study_type(self):
        probands = self.study_filters.get_matching_probands_by_study_type(
            "CNV")
        self.assertEquals(858, len(probands))

    def test_get_matching_probands_by_bad_study_name(self):
        with self.assertRaises(AssertionError):
            self.study_filters.get_matching_probands_by_study("ala bala")

    def test_get_matching_probands_by_study_name(self):
        probands = self.study_filters.get_matching_probands_by_study(
            "LevyCNV2011")

        self.assertEquals(858, len(probands))
