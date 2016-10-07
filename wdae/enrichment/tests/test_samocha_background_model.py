'''
Created on Aug 2, 2016

@author: lubo
'''
import os
import unittest

from django.conf import settings

from DAE import get_gene_sets_symNS
from enrichment.background import SamochaBackground
import numpy as np
import pandas as pd


class Test(unittest.TestCase):

    def setUp(self):
        self.gene_term = get_gene_sets_symNS('main')
        self.gene_syms = self.gene_term.t2G['ChromatinModifiers'].keys()

    def test_compare_two_background_tables(self):
        background = SamochaBackground()
        df1 = background.background
        self.assertIsNotNone(df1)

        filename = os.path.join(
            settings.BASE_DIR,
            '..',
            'data/enrichment/background-samocha-et-al.csv'
        )
        df2 = pd.read_csv(filename)
        self.assertIsNotNone(df2)

        self.assertTrue(np.all(df1['gene'] == df2['gene_upper']))
        self.assertTrue(np.all(df1['M'] == df2['M']))
        self.assertTrue(np.all(df1['F'] == df2['F']))

        index = np.abs(df1['P_LGDS'] - df2['P_LGDS']) > 1E-8
        self.assertFalse(np.any(index))
        index = np.abs(df1['P_LGDS'] - df2['P_LGDS']) < 1E-8
        self.assertTrue(np.all(index))

        index = np.abs(df1['P_MISSENSE'] - df2['P_MISSENSE']) < 1E-8
        self.assertTrue(np.all(index))

        index = np.abs(df1['P_SYNONYMOUS'] - df2['P_SYNONYMOUS']) < 1E-8
        self.assertTrue(np.all(index))

#     def test_enrichment_test(self):
#         expected, p_val = self.bg.test(
#             10, 10, 'LGDs', self.gene_syms, 3367, 596)
#         self.assertIsNotNone(expected)
#         self.assertIsNotNone(p_val)
#
#     def test_effect_types_does_not_throw(self):
#         self.bg.test(10, 10, 'LGDs', self.gene_syms, 3367, 596)
#         self.bg.test(10, 10, 'missense', self.gene_syms, 3367, 596)
#         self.bg.test(10, 10, 'synonymous', self.gene_syms, 3367, 596)
#
#     def test_wrong_effect_types_does_throw(self):
#         with self.assertRaises(AssertionError):
#             self.bg.test(10, 10, 'ala bala', self.gene_syms, 3367, 596)
#         with self.assertRaises(AssertionError):
#             self.bg.test(10, 10, 'frame-shift', self.gene_syms, 3367, 596)
#         with self.assertRaises(AssertionError):
#             self.bg.test(10, 10, 'splice-site', self.gene_syms, 3367, 596)
#
#     def test_example_calculation_lgds(self):
#         expected, p_val = self.bg.test(
#             46, 546, 'LGDs', self.gene_syms, 3367, 596)
#         print("expected: {}; p_val: {}".format(expected, p_val))
#         self.assertAlmostEquals(12.57, expected, 1)
#         self.assertAlmostEquals(8E-49, p_val, 10)
#
#     def test_example_calculation_missense(self):
#         expected, p_val = self.bg.test(
#             95, 2583, 'missense', self.gene_syms, 3367, 596)
#         print("expected: {}; p_val: {}".format(expected, p_val))
#         self.assertAlmostEquals(85.85, expected, 1)
#         self.assertAlmostEquals(0.34940690, p_val, 5)
