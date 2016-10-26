'''
Created on Sep 30, 2016

@author: lubo
'''
import unittest
from enrichment.counters import DenovoStudies, GeneEventsCounter
from DAE import get_gene_sets_symNS
import precompute
from enrichment.families import ChildrenStats
from enrichment.background import SamochaBackground


class SynonymousBackgroundStatsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SynonymousBackgroundStatsTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['chromatin modifiers'].keys()

        cls.background = precompute.register.get('synonymousBackgroundModel')
        cls.children_stats = ChildrenStats.build(cls.denovo_studies)

    def test_stats_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        events = counter.events(self.denovo_studies)

        stats = self.background.calc_stats(
            events, self.gene_set,
            self.children_stats['autism'])

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(17.7123, stats.all_expected, 2)
        self.assertAlmostEqual(8.3E-05, stats.all_pvalue, 4)

        self.assertAlmostEqual(1.265169, stats.rec_expected, 2)
        self.assertAlmostEqual(3.5E-06, stats.rec_pvalue, 4)

        self.assertAlmostEqual(14.85763, stats.male_expected, 2)
        self.assertAlmostEqual(0.0021, stats.male_pvalue, 4)

        self.assertAlmostEqual(3.47, stats.female_expected, 2)
        self.assertAlmostEqual(4.6E-05, stats.female_pvalue, 4)

    def test_stats_schizophrenia_with_effect_type_lgd(self):
        counter = GeneEventsCounter('schizophrenia', 'LGDs')

        events = counter.events(self.denovo_studies)

        stats = self.background.calc_stats(
            events, self.gene_set,
            self.children_stats['schizophrenia'])

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(3.02, stats.all_expected, 2)
        self.assertAlmostEqual(0.128851, stats.all_pvalue, 4)

        self.assertAlmostEqual(0.06, stats.rec_expected, 2)
        self.assertAlmostEqual(1, stats.rec_pvalue, 4)

        self.assertAlmostEqual(1.56, stats.male_expected, 2)
        self.assertAlmostEqual(0.0698, stats.male_pvalue, 4)

        self.assertAlmostEqual(1.46, stats.female_expected, 2)
        self.assertAlmostEqual(0.6579, stats.female_pvalue, 4)

    def test_stats_unaffected_with_effect_type_missense(self):
        counter = GeneEventsCounter('unaffected', 'missense')

        events = counter.events(self.denovo_studies)

        stats = self.background.calc_stats(
            events, self.gene_set,
            self.children_stats['unaffected'])

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(43.924, stats.all_expected, 2)
        self.assertAlmostEqual(0.81817466, stats.all_pvalue, 4)

        self.assertAlmostEqual(3.665747, stats.rec_expected, 2)
        self.assertAlmostEqual(0.7875, stats.rec_pvalue, 4)

        self.assertAlmostEqual(20.69687, stats.male_expected, 2)
        self.assertAlmostEqual(0.8228654, stats.male_pvalue, 4)

        self.assertAlmostEqual(25.368269, stats.female_expected, 2)
        self.assertAlmostEqual(0.47852, stats.female_pvalue, 4)


class SamochaBackgroundStatsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SamochaBackgroundStatsTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['chromatin modifiers'].keys()

        cls.background = precompute.register.get('samochaBackgroundModel')
        cls.children_stats = ChildrenStats.build(cls.denovo_studies)

    def test_stats_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        events = counter.events(self.denovo_studies)

        stats = self.background.calc_stats(
            events, self.gene_set,
            self.children_stats['autism'])

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(12.5358, stats.all_expected, 2)
        self.assertAlmostEqual(0.0, stats.all_pvalue, 4)

        self.assertAlmostEqual(0.89924, stats.rec_expected, 2)
        self.assertAlmostEqual(0.0, stats.rec_pvalue, 4)

        self.assertAlmostEqual(10.65059, stats.male_expected, 2)
        self.assertAlmostEqual(0.0, stats.male_pvalue, 4)

        self.assertAlmostEqual(1.8831, stats.female_expected, 2)
        self.assertAlmostEqual(2E-07, stats.female_pvalue, 4)
