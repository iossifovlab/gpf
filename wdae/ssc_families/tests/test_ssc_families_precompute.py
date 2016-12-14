'''
Created on Jul 7, 2016

@author: lubo
'''
import unittest
from ssc_families.ssc_families_precompute import SSCFamiliesPrecompute
from helpers.default_ssc_study import get_ssc_denovo_studies


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.precompute = SSCFamiliesPrecompute()
        self.precompute.precompute()

    def test_quads_precompute(self):
        self.assertIsNotNone(self.precompute.quads())
        self.assertEquals(141, len(self.precompute.quads()))
        self.assertEquals(2724, len(self.precompute.nonquads()))

    def test_build_quads(self):
        studies = get_ssc_denovo_studies()

        quads, nonquads = self.precompute._build_quads(studies)
        self.assertEquals(141, len(quads))
        self.assertEquals(2724, len(nonquads))

    def test_iossifov2014we_quads(self):
        self.assertEquals(
            1902, len(self.precompute.quads('IossifovWE2014')))
        self.assertEquals(
            615, len(self.precompute.nonquads('IossifovWE2014')))

    def test_we_quads(self):
        self.assertEquals(
            1899, len(self.precompute.quads('we')))
        self.assertEquals(
            627, len(self.precompute.nonquads('we')))

    def test_cnv_quads(self):
        self.assertEquals(
            2224, len(self.precompute.quads('cnv')))
        self.assertEquals(
            632, len(self.precompute.nonquads('cnv')))
