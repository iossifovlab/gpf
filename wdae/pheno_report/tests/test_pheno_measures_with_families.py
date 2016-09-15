'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno_report.measures import NormalizedMeasure, Measures
from pheno_families.pheno_filter import PhenoMeasureFilters


class HeadCircumferenceTest(unittest.TestCase):

    def setUp(self):
        self.measure = NormalizedMeasure(
            'ssc_commonly_used.head_circumference')

    def test_pheno_measure_created(self):
        measure = self.measure
        self.assertIsNotNone(measure)

    def test_pheno_measure_check_df(self):
        measure = self.measure
        df = measure.df
        self.assertIn('family_id', df.columns)
        self.assertIn('person_id', df.columns)
        self.assertIn('pheno_common.age', df.columns)
        self.assertIn('pheno_common.non_verbal_iq', df.columns)

        self.assertIn('ssc_commonly_used.head_circumference', df.columns)


class FamilyIdsByPhenoMeasure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.measures = Measures()
        cls.measures.load()
        cls.pheno_measure = PhenoMeasureFilters()

    def test_verbal_iq_interval(self):
        family_ids = self.measures.get_measure_families(
            'pheno_common.verbal_iq', 10, 20)
        self.assertEquals(120, len(family_ids))
        df = self.measures.get_measure_df('pheno_common.verbal_iq')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['pheno_common.verbal_iq'].values <= 20))
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['pheno_common.verbal_iq'].values >= 10))

    def test_head_circumference_interval(self):
        family_ids = self.measures.get_measure_families(
            'ssc_commonly_used.head_circumference', 49, 50)
        self.assertEquals(102, len(family_ids))
        df = self.measures.get_measure_df(
            'ssc_commonly_used.head_circumference')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] == family_id][
                    'ssc_commonly_used.head_circumference'].values <= 50))
            self.assertTrue(
                all(df[df['family_id'] == family_id][
                    'ssc_commonly_used.head_circumference'].values >= 49))

    def test_verbal_iq_interval_with_family_counters(self):
        proband_ids = self.measures.get_measure_probands(
            'pheno_common.verbal_iq', 10, 20)

        self.assertEquals(120, len(proband_ids))
        df = self.measures.get_measure_df('pheno_common.verbal_iq')
        for proband_id in proband_ids:
            self.assertTrue(
                all(df[df['person_id'] ==
                       proband_id]['pheno_common.verbal_iq'].values <= 20))
            self.assertTrue(
                all(df[df['person_id'] ==
                       proband_id]['pheno_common.verbal_iq'].values >= 10))

        pids = self.pheno_measure.get_matching_probands(
            'pheno_common.verbal_iq', 10, 20)

        self.assertEquals(set([]), (pids - set(proband_ids)))
