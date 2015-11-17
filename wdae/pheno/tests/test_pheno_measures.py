'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno.measures import NormalizedMeasure


class Test(unittest.TestCase):

    def setUp(self):
        self.measure = NormalizedMeasure('head_circumference')

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

if __name__ == "__main__":
    unittest.main()
