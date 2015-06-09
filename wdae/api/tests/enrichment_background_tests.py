'''
Created on Jun 9, 2015

@author: lubo
'''
import unittest
import numpy as np
from api.enrichment.background import SynonymousBackground


class SynonymousBackgroundTest(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_synonymous_background(self):
        synbg = SynonymousBackground()
        bg = synbg.precompute()
        self.assertEquals(213494, np.sum(bg['raw']))
        self.assertAlmostEqual(1.0, np.sum(bg['weight']), 5)

    def test_synonymous_background_serialize_deserialize(self):
        synbg = SynonymousBackground()
        synbg.precompute()
        
        data = synbg.serialize()
        
        synbg2 = SynonymousBackground()
        synbg2.deserialize(data)
        
        self.assertTrue(np.array_equal(synbg.background,
                                       synbg2.background))
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()