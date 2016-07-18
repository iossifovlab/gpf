'''
Created on Jul 7, 2016

@author: lubo
'''


import unittest
from ssc_families.ssc_filter import QuadFamiliesFilter, FamiliesGenderFilter


class QuadFamiliesFilterTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.quad_filter = QuadFamiliesFilter()

    def test_quad_filter_by_study(self):
        families = self.quad_filter.get_matching_families(
            study_type=None, study_name='IossifovWE2014')
        self.assertEquals(1902, len(families))

    def test_quad_filter_by_study_type(self):
        families = self.quad_filter.get_matching_families(
            study_type='cnv', study_name=None)
        self.assertEquals(2351, len(families))

    def test_quad_filter_by_study_and_study_type(self):
        families = self.quad_filter.get_matching_families(
            study_type='cnv', study_name='IossifovWE2014')
        self.assertEquals(1890, len(families))


class GenderFamiliesFilterTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.gender_filter = FamiliesGenderFilter()
        self.quad_filter = QuadFamiliesFilter()

    def test_filter_probands_gender(self):
        families = self.quad_filter.get_matching_families(
            'cnv', 'IossifovWE2014')
        self.assertEquals(1890, len(families))

        male_probands = self.gender_filter.filter_matching_probands(
            families, 'M')
        female_probands = self.gender_filter.filter_matching_probands(
            families, 'F')

        self.assertEquals(1655, len(male_probands))
        self.assertEquals(235, len(female_probands))
