'''
Created on Jul 7, 2016

@author: lubo
'''
import unittest
from ssc_families.ssc_families_precompute import SSCFamiliesPrecompute
from api.default_ssc_study import get_ssc_denovo_studies


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.precompute = SSCFamiliesPrecompute()
        self.precompute.precompute()

    def test_quads_precompute(self):
        self.assertIsNotNone(self.precompute.quads())
        self.assertEquals(417, len(self.precompute.quads()))
        self.assertEquals(1954, len(self.precompute.mismatched_quads()))

    def test_build_quads(self):
        studies = get_ssc_denovo_studies()

        quads, mismatched = self.precompute._build_quads(studies)
        self.assertEquals(417, len(quads))
        self.assertEquals(1954, len(mismatched))

    def test_iossifov2014we_quads(self):
        self.assertEquals(
            1902, len(self.precompute.quads('IossifovWE2014')))
        self.assertEquals(
            0, len(self.precompute.mismatched_quads('IossifovWE2014')))
