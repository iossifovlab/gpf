'''
Created on Jun 19, 2015

@author: lubo
'''
import unittest
from enrichment.background import CodingLenBackground
from DAE import get_gene_sets_symNS

import numpy as np


class Test(unittest.TestCase):

    def setUp(self):
        self.gene_term = get_gene_sets_symNS('main')
        self.gene_syms = self.gene_term.t2G['FMRP-Tuschl'].keys()

    def tearDown(self):
        pass

    def test_load(self):
        background = CodingLenBackground()
        bg = background._load_and_prepare_build()
        self.assertTrue(bg is not None)

    def test_max_sym_len(self):
        background = CodingLenBackground()
        bg = background._load_and_prepare_build()

        max_sym_len = max([len(s) for (s, _l) in bg])
        self.assertTrue(max_sym_len < 32)

    def test_precompute(self):
        background = CodingLenBackground()
        bg = background.precompute()
        self.assertTrue(bg is not None)

        self.assertTrue(background.is_ready)

    def test_total(self):
        background = CodingLenBackground()
        background.precompute()
        self.assertEquals(33100101, background.total)

    def test_count(self):
        background = CodingLenBackground()
        background.precompute()
        self.assertEquals(3395921, background.count(self.gene_syms))

    def test_prob(self):
        background = CodingLenBackground()
        background.precompute()
        self.assertAlmostEqual(0.10259, background.prob(self.gene_syms), 4)

    def test_serialize_deserialize(self):
        background = CodingLenBackground()
        background.precompute()

        data = background.serialize()

        b2 = CodingLenBackground()
        b2.deserialize(data)

        np.testing.assert_array_equal(background.background, b2.background)


if __name__ == "__main__":
    unittest.main()
