'''
Created on Jun 9, 2015

@author: lubo
'''
import unittest
import numpy as np
from api.enrichment.background import SynonymousBackground


class SynonymousBackgroundTest(unittest.TestCase):

    def test_synonymous_background(self):
        synbg = SynonymousBackground()
        bg = synbg.precompute()
        self.assertEquals(211645, np.sum(bg['raw']))
#         self.assertAlmostEqual(1.0, np.sum(bg['weight']), 5)
