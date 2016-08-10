'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno_report.measures import NormalizedMeasure, Measures
from pheno_families.pheno_filter import PhenoMeasureFilters


class HeadCircumferenceTest(unittest.TestCase):

    def setUp(self):
        self.measure = NormalizedMeasure('head_circumference')

    def test_pheno_measure_created(self):
        measure = self.measure
        self.assertIsNotNone(measure)

    def test_pheno_measure_check_df(self):
        measure = self.measure
        df = measure.df
        self.assertIn('family_id', df.columns)
        self.assertIn('individual', df.columns)
        self.assertIn('age', df.columns)
        self.assertIn('non_verbal_iq', df.columns)
        self.assertIn('verbal_iq', df.columns)

        self.assertIn('head_circumference', df.columns)


class FamilyIdsByPhenoMeasure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.measures = Measures()
        cls.measures.load()
        cls.pheno_measure = PhenoMeasureFilters()

    def test_verbal_iq_interval(self):
        family_ids = self.measures.get_measure_families('verbal_iq', 10, 20)
        self.assertEquals(120, len(family_ids))
        df = self.measures.get_measure_df('verbal_iq')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['verbal_iq'].values <= 20))
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['verbal_iq'].values >= 10))

    def test_head_circumference_interval(self):
        family_ids = self.measures.get_measure_families(
            'head_circumference', 49, 50)
        self.assertEquals(102, len(family_ids))
        df = self.measures.get_measure_df('head_circumference')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['head_circumference'].values <= 50))
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['head_circumference'].values >= 49))

    def test_verbal_iq_interval_with_family_counters(self):
        proband_ids = self.measures.get_measure_probands('verbal_iq', 10, 20)

        self.assertEquals(120, len(proband_ids))
        df = self.measures.get_measure_df('verbal_iq')
        for proband_id in proband_ids:
            self.assertTrue(
                all(df[df['individual'] ==
                       proband_id]['verbal_iq'].values <= 20))
            self.assertTrue(
                all(df[df['individual'] ==
                       proband_id]['verbal_iq'].values >= 10))

        pids = self.pheno_measure.get_matching_probands('verbal_iq', 10, 20)

        self.assertEquals(set([]), (pids - set(proband_ids)))
