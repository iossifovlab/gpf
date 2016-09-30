'''
Created on Sep 30, 2016

@author: lubo
'''
import unittest
from enrichment.counters import DenovoStudies, GeneEventsCounter
from DAE import get_gene_sets_symNS
import precompute


class SynonymousBackgroundStatsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SynonymousBackgroundStatsTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

        cls.background = precompute.register.get('synonymousBackgroundModel')

    def test_stats_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        all_events, enriched_events = counter.full_events(
            self.denovo_studies, self.gene_set)

        stats = self.background.calc_stats(
            all_events, enriched_events, self.gene_set)

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(17.70, stats.all_expected, 2)
        self.assertAlmostEqual(8.3E-05, stats.all_pvalue, 4)

        self.assertAlmostEqual(1.26, stats.rec_expected, 2)
        self.assertAlmostEqual(3.5E-06, stats.rec_pvalue, 4)

        self.assertAlmostEqual(14.85, stats.male_expected, 2)
        self.assertAlmostEqual(0.0021, stats.male_pvalue, 4)

        self.assertAlmostEqual(3.47, stats.female_expected, 2)
        self.assertAlmostEqual(4.6E-05, stats.female_pvalue, 4)

    def test_stats_schizophrenia_with_effect_type_lgd(self):
        counter = GeneEventsCounter('schizophrenia', 'LGDs')

        all_events, enriched_events = counter.full_events(
            self.denovo_studies, self.gene_set)

        stats = self.background.calc_stats(
            all_events, enriched_events, self.gene_set)

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(3.02, stats.all_expected, 2)
        self.assertAlmostEqual(0.1288, stats.all_pvalue, 4)

        self.assertAlmostEqual(0.06, stats.rec_expected, 2)
        self.assertAlmostEqual(1, stats.rec_pvalue, 4)

        self.assertAlmostEqual(1.56, stats.male_expected, 2)
        self.assertAlmostEqual(0.0698, stats.male_pvalue, 4)

        self.assertAlmostEqual(1.46, stats.female_expected, 2)
        self.assertAlmostEqual(0.6579, stats.female_pvalue, 4)

    def test_stats_unaffected_with_effect_type_missense(self):
        counter = GeneEventsCounter('unaffected', 'missense')

        all_events, enriched_events = counter.full_events(
            self.denovo_studies, self.gene_set)

        stats = self.background.calc_stats(
            all_events, enriched_events, self.gene_set)

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(43.90, stats.all_expected, 2)
        self.assertAlmostEqual(0.8181, stats.all_pvalue, 4)

        self.assertAlmostEqual(3.66, stats.rec_expected, 2)
        self.assertAlmostEqual(0.7875, stats.rec_pvalue, 4)

        self.assertAlmostEqual(20.69, stats.male_expected, 2)
        self.assertAlmostEqual(0.8228, stats.male_pvalue, 4)

        self.assertAlmostEqual(25.36, stats.female_expected, 2)
        self.assertAlmostEqual(0.4201, stats.female_pvalue, 4)


class SamochaBackgroundStatsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SamochaBackgroundStatsTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

        cls.background = precompute.register.get('samochaBackgroundModel')

    def test_stats_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        all_events, enriched_events = counter.full_events(
            self.denovo_studies, self.gene_set)

        stats = self.background.calc_stats(
            all_events, enriched_events, self.gene_set)

        self.assertIsNotNone(stats)

        self.assertAlmostEqual(1.79, stats.all_expected, 2)
        self.assertAlmostEqual(0.0, stats.all_pvalue, 4)

        self.assertAlmostEqual(0.125, stats.rec_expected, 2)
        self.assertAlmostEqual(3.5E-06, stats.rec_pvalue, 4)

        self.assertAlmostEqual(1.447, stats.male_expected, 2)
        self.assertAlmostEqual(0.0, stats.male_pvalue, 4)

        self.assertAlmostEqual(0.3476, stats.female_expected, 2)
        self.assertAlmostEqual(4.6E-05, stats.female_pvalue, 4)
