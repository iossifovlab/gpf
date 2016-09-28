'''
Created on Aug 2, 2016

@author: lubo
'''
import unittest
from DAE import get_gene_sets_symNS
from enrichment.background import SamochaBackground


class CreateTest(unittest.TestCase):

    def test_create(self):
        background = SamochaBackground()
        self.assertTrue(background.is_ready)


class Test(unittest.TestCase):

    def setUp(self):
        self.bg = SamochaBackground()
        self.gene_term = get_gene_sets_symNS('main')
        self.gene_syms = self.gene_term.t2G['ChromatinModifiers'].keys()

    def test_enrichment_test(self):
        expected, p_val = self.bg.test(
            10, 10, 'LGDs', self.gene_syms, 3367, 596)
        self.assertIsNotNone(expected)
        self.assertIsNotNone(p_val)

    def test_effect_types_does_not_throw(self):
        self.bg.test(10, 10, 'LGDs', self.gene_syms, 3367, 596)
        self.bg.test(10, 10, 'missense', self.gene_syms, 3367, 596)
        self.bg.test(10, 10, 'synonymous', self.gene_syms, 3367, 596)

    def test_wrong_effect_types_does_throw(self):
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'ala bala', self.gene_syms, 3367, 596)
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'frame-shift', self.gene_syms, 3367, 596)
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'splice-site', self.gene_syms, 3367, 596)

    def test_example_calculation_lgds(self):
        expected, p_val = self.bg.test(
            46, 546, 'LGDs', self.gene_syms, 3367, 596)
        print("expected: {}; p_val: {}".format(expected, p_val))
        self.assertAlmostEquals(12.57, expected, 1)
        self.assertAlmostEquals(8E-49, p_val, 10)

    def test_example_calculation_missense(self):
        expected, p_val = self.bg.test(
            95, 2583, 'missense', self.gene_syms, 3367, 596)
        print("expected: {}; p_val: {}".format(expected, p_val))
        self.assertAlmostEquals(85.85, expected, 1)
        self.assertAlmostEquals(0.34940690, p_val, 5)
