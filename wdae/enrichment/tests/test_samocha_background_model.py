'''
Created on Aug 2, 2016

@author: lubo
'''
import unittest
from DAE import get_gene_sets_symNS
from enrichment.background import SamochaBackground


class CreateTest(unittest.TestCase):

    def setUp(self):
        self.gene_term = get_gene_sets_symNS('main')
        self.gene_syms = self.gene_term.t2G['FMRP-Tuschl'].keys()

    def tearDown(self):
        pass

    def test_create(self):
        background = SamochaBackground()
        self.assertTrue(background.is_ready)


class Test(unittest.TestCase):

    def setUp(self):
        self.bg = SamochaBackground()
        self.gene_term = get_gene_sets_symNS('main')
        self.gene_syms = self.gene_term.t2G['FMRP-Tuschl'].keys()

    def test_enrichment_test(self):
        expected, p_val = self.bg.test(10, 10, 'LGDs', self.gene_syms)
        self.assertIsNotNone(expected)
        self.assertIsNotNone(p_val)

    def test_effect_types_does_not_throw(self):
        self.bg.test(10, 10, 'LGDs', self.gene_syms)
        self.bg.test(10, 10, 'missense', self.gene_syms)
        self.bg.test(10, 10, 'synonymous', self.gene_syms)

    def test_wrong_effect_types_does_throw(self):
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'ala bala', self.gene_syms)
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'frame-shift', self.gene_syms)
        with self.assertRaises(AssertionError):
            self.bg.test(10, 10, 'splice-site', self.gene_syms)
