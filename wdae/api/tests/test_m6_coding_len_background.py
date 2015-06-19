'''
Created on Jun 19, 2015

@author: lubo
'''
import unittest
from api.enrichment.background import CodingLenBackground


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_load(self):
        background = CodingLenBackground()
        bg = background._load_and_prepare_build()
        self.assertTrue(bg is not None)
        
    
    def test_max_sym_len(self):
        background = CodingLenBackground()
        bg = background._load_and_prepare_build()
        
        max_sym_len = max([len(s) for (s,_l) in bg])
        print("max gene sym len: {}".format(max_sym_len))
        self.assertTrue(max_sym_len<32)
        
    def test_precompute(self):
        background = CodingLenBackground()
        bg = background.precompute()
        self.assertTrue(bg is not None)
        
        self.assertTrue(background.is_ready)
        
    def test_total(self):
        background = CodingLenBackground()
        background.precompute()
        self.assertEquals(33100101, background.total)    
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()