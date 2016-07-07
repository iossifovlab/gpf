'''
Created on Jul 7, 2016

@author: lubo
'''
import unittest
from ssc_families.ssc_families_precompute import SSCFamiliesPrecompute


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.precompute = SSCFamiliesPrecompute()

    def test_quads_precompute(self):
        self.precompute.precompute()
        self.assertIsNotNone(self.precompute.quads())
        self.assertEquals(2371, len(self.precompute.quads()))
        self.assertEquals(0, len(self.precompute.mismatched_quads()))
