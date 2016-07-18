'''
Created on Jun 29, 2016

@author: lubo
'''
import unittest
from pheno_families.pheno_filter import PhenoMeasureFilters, StudyFilter,\
    RaceFilter


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

    def test_filter_matching_probands(self):
        prbs1 = self.pheno_filters.get_matching_probands(
            "non_verbal_iq")
        self.assertEquals(2756, len(prbs1))

        prbs = self.pheno_filters.filter_matching_probands(
            prbs1, "non_verbal_iq", 9, 10)
        self.assertEquals(1, len(prbs))


class PhenoStudyFilterTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.study_filters = StudyFilter()

    def test_get_matching_probands_by_study_type(self):
        probands = self.study_filters.get_matching_probands_by_study_type(
            "CNV")
        self.assertEquals(2850, len(probands))

    def test_get_matching_probands_by_bad_study_name(self):
        with self.assertRaises(AssertionError):
            self.study_filters.get_matching_probands_by_study("ala bala")

    def test_get_matching_probands_by_study_name(self):
        probands = self.study_filters.get_matching_probands_by_study(
            "LevyCNV2011")

        self.assertEquals(858, len(probands))

    def test_filter_matching_probadnds_by_study_name(self):
        prbs1 = self.study_filters.get_matching_probands_by_study(
            "LevyCNV2011")
        prbs2 = self.study_filters.get_matching_probands_by_study(
            "IossifovWE2014")

        self.assertEquals(858, len(prbs1))
        self.assertEquals(2508, len(prbs2))

        prbs = self.study_filters.filter_matching_probands_by_study(
            prbs2, "LevyCNV2011")
        self.assertEquals(771, len(prbs))

    def test_filter_matching_probands_by_study_type(self):
        prbs1 = self.study_filters.get_matching_probands_by_study(
            "LevyCNV2011")
        prbs = self.study_filters.filter_matching_probands_by_study_type(
            prbs1, "TG")
        self.assertEquals(768, len(prbs))


class PhenoRaceFilterTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.study_filters = StudyFilter()
        self.race_filter = RaceFilter()

    def test_white_race(self):
        res = self.race_filter.get_matching_families_by_race('other')
        self.assertIsNotNone(res)

        probands = self.study_filters.get_matching_probands_by_study(
            "LevyCNV2011")
        res = self.race_filter.filter_matching_probands_by_race(
            'other', probands)
        self.assertEquals(14, len(res))
