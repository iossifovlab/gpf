'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
# import numpy as np
from preloaded.register import get_register


class GeneWeightsRVISTest(unittest.TestCase):

    def setUp(self):
        register = get_register()
        self.weights = register.get('gene_weights')

    def test_nan(self):
        w = self.weights.get_weight('RVIS_rank')
        self.assertIsNotNone(w)

#     def test_get_genes_by_weight(self):
#         genes = self.weights.get_genes_by_weight('RVIS',
#                                                  wmin=-0.0001,
#                                                  wmax=0.0001)
#         self.assertEqual(94, len(genes))
#
#         genes = self.weights.get_genes_by_weight('RVIS',
#                                                  wmin=0.0,
#                                                  wmax=0.0)
#         self.assertEqual(94, len(genes))
#
#     def test_get_genes_by_weight_check_nan(self):
#         df = self.weights.df
#         genes = self.weights.get_genes_by_weight('RVIS',
#                                                  wmin=0.0,
#                                                  wmax=0.0)
#         for g in genes:
#             [rv] = df[df.gene == g]['RVIS'].values
#             self.assertFalse(np.isnan(rv))

#     def test_get_genes_by_weight_check_all_nan(self):
#         df = self.weights.df
#         genes = self.weights.get_genes_by_weight('RVIS',
#                                                  wmin=None,
#                                                  wmax=None)
#         for g in genes:
#             [rv] = df[df.gene == g]['RVIS'].values
#             self.assertFalse(np.isnan(rv))


if __name__ == "__main__":
    unittest.main()
