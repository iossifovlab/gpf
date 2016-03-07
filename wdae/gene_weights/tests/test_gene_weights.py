'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from gene_weights.weights import Weights


class GeneWeightsTest(unittest.TestCase):

    def setUp(self):
        self.weights = Weights()
        self.weights.load()

    def tearDown(self):
        pass

    def test_weights_created(self):
        self.assertIsNotNone(self.weights)

    def test_lgd_rank_available(self):
        self.assertTrue(self.weights.has_weight('LGD_rank'))

    def test_get_lgd_rand(self):
        w = self.weights.get_weight('LGD_rank')
        self.assertIsNotNone(w)
        self.assertAlmostEqual(1.0, w.min(), delta=0.01)
        self.assertAlmostEqual(23949.0, w.max(), delta=0.01)

    def test_get_genes_by_weight(self):
        g = self.weights.get_genes_by_weight('LGD_rank', 1.5, 5.0)
        self.assertEqual(4, len(g))

        g = self.weights.get_genes_by_weight('LGD_rank', -1, 5.0)
        self.assertEqual(5, len(g))

        g = self.weights.get_genes_by_weight('LGD_rank', 1.0, 5.0)
        self.assertEqual(5, len(g))


if __name__ == "__main__":
    unittest.main()
