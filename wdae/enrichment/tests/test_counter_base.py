'''
Created on Sep 30, 2016

@author: lubo
'''

import unittest

from enrichment.counters import CounterBase, DenovoStudies


class CounterBaseTest(unittest.TestCase):

    def test_variants_unaffected_with_effect_type_lgd(self):
        counter = CounterBase('unaffected', 'LGDs')
        denovo_studies = DenovoStudies()

        variants = counter.get_variants(denovo_studies)
        self.assertIsNotNone(variants)

        count = 0
        for v in variants:
            self.assertIn('sib', v.inChS)
            count += 1
        print(count)
        self.assertEquals(243, count)

    def test_variants_unaffected_with_effect_type_missense(self):
        counter = CounterBase('unaffected', 'Missense')
        denovo_studies = DenovoStudies()

        variants = counter.get_variants(denovo_studies)
        self.assertIsNotNone(variants)

        count = 0
        for v in variants:
            self.assertIn('sib', v.inChS)
            self.assertEquals('missense', v.requestedGeneEffects[0]['eff'])
            count += 1
        print(count)
        self.assertEquals(1616, count)

    def test_variants_unaffected_with_effect_type_synonimous(self):
        counter = CounterBase('unaffected', 'synonymous')
        denovo_studies = DenovoStudies()

        variants = counter.get_variants(denovo_studies)
        self.assertIsNotNone(variants)

        count = 0
        for v in variants:
            self.assertIn('sib', v.inChS)
            self.assertEquals('synonymous', v.requestedGeneEffects[0]['eff'])
            count += 1
        print(count)
        self.assertEquals(686, count)

    def test_variants_autism_with_effect_type_lgd(self):
        counter = CounterBase('autism', 'LGDs')
        denovo_studies = DenovoStudies()

        variants = counter.get_variants(denovo_studies)
        self.assertIsNotNone(variants)

        count = 0
        for v in variants:
            self.assertIn('prb', v.inChS)
            count += 1
        print(count)
        self.assertEquals(607, count)

    def test_all_events_not_implemented(self):
        counter = CounterBase('autism', 'LGDs')
        denovo_studies = DenovoStudies()
        with self.assertRaises(NotImplementedError):
            counter.all_events(denovo_studies, [])
