'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno.measures import NormalizedMeasure


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
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

if __name__ == "__main__":
    unittest.main()
