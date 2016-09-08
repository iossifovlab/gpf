'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno_report.measures import NormalizedMeasure, Measures


class HeadCircumferenceTest(unittest.TestCase):

    def setUp(self):
        self.measure = NormalizedMeasure(
            'ssc_commonly_used', 'head_circumference')

    def test_pheno_measure_created(self):
        measure = self.measure
        self.assertIsNotNone(measure)

    def test_pheno_measure_check_df(self):
        measure = self.measure
        df = measure.df
        self.assertIn('family_id', df.columns)
        self.assertIn('age', df.columns)
        self.assertIn('non_verbal_iq', df.columns)
        self.assertIn('verbal_iq', df.columns)

        self.assertIn('head_circumference', df.columns)

    def test_pheno_measure_normalize_by_age(self):
        measure = self.measure
        fitted = measure.normalize(['age'])
        self.assertIsNotNone(fitted)

    def test_pheno_measure_normalize_by_couple(self):
        measure = self.measure
        fitted = measure.normalize(['age', 'verbal_iq'])
        self.assertIsNotNone(fitted)

    def test_pheno_measure_normalize_by_single_wrong_value(self):
        measure = self.measure
        with self.assertRaises(AssertionError):
            measure.normalize(['ala_bala_portokala'])

    def test_pheno_measure_normalize_by_mixed_wrong_value(self):
        measure = self.measure
        with self.assertRaises(AssertionError):
            measure.normalize(['age', 'ala_bala_portokala'])


class VerbalIqTest(unittest.TestCase):

    def setUp(self):
        self.measure = NormalizedMeasure('core', 'verbal_iq')

    def test_pheno_measure_created(self):
        measure = self.measure
        self.assertIsNotNone(measure)

    def test_pheno_measure_check_df(self):
        measure = self.measure
        df = measure.df
        self.assertIn('family_id', df.columns)
        self.assertIn('age', df.columns)
        self.assertIn('non_verbal_iq', df.columns)
        self.assertIn('verbal_iq', df.columns)

    def test_pheno_measure_normalize_by_verbal_iq(self):
        measure = self.measure
        measure.normalize(['verbal_iq'])
        df = measure.df
        self.assertIn('family_id', df.columns)
        self.assertIn('age', df.columns)
        self.assertIn('non_verbal_iq', df.columns)
        self.assertIn('verbal_iq', df.columns)


class FamilyIdsByPhenoMeasure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(FamilyIdsByPhenoMeasure, cls).setUpClass()
        cls.measures = Measures()
        cls.measures.load()

    def test_verbal_iq_interval(self):
        family_ids = self.measures.get_measure_families(
            'core', 'verbal_iq', 10, 20)
        self.assertEquals(120, len(family_ids))
        df = self.measures.get_measure_df(
            'core', 'verbal_iq')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['verbal_iq'].values <= 20))
            self.assertTrue(
                all(df[df['family_id'] ==
                       family_id]['verbal_iq'].values >= 10))

    def test_head_circumference_interval(self):
        family_ids = self.measures.get_measure_families(
            'ssc_commonly_used', 'head_circumference', 49, 50)
        self.assertEquals(102, len(family_ids))
        df = self.measures.get_measure_df(
            'ssc_commonly_used', 'head_circumference')
        for family_id in family_ids:
            self.assertTrue(
                all(df[df['family_id'] == family_id][
                    'head_circumference'].values <= 50))
            self.assertTrue(
                all(df[df['family_id'] == family_id][
                    'head_circumference'].values >= 49))


class PhenoMeasureRowCount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(PhenoMeasureRowCount, cls).setUpClass()
        cls.measures = Measures()
        cls.measures.load()

    def test_verbal_iq_count(self):
        df = self.measures.get_measure_df('core', 'verbal_iq')
        self.assertEquals(2757, len(df))

    def test_head_circumference(self):
        df = self.measures.get_measure_df(
            'ssc_commonly_used', 'head_circumference')
        self.assertEquals(2728, len(df))

#     def test_cbcl_2_5_total_problems(self):
#         df = self.measures.get_measure_df('cbcl_2_5_total_problems')
#         self.assertEquals(655, len(df))
