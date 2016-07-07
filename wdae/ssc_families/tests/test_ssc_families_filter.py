'''
Created on Jul 7, 2016

@author: lubo
'''


import unittest
from ssc_families.ssc_filter import QuadFamiliesFilter


class Test(unittest.TestCase):

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
        self.assertEquals(628, len(families))

    def test_quad_filter_by_study_and_study_type(self):
        families = self.quad_filter.get_matching_families(
            study_type='cnv', study_name='IossifovWE2014')
        self.assertEquals(474, len(families))
