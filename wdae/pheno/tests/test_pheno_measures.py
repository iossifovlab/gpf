'''
Created on Nov 17, 2015

@author: lubo
'''
import unittest
from pheno.measures import NormalizedMeasure


class Test(unittest.TestCase):

    def test_pheno_measure_data_frame(self):
        measure = NormalizedMeasure('head_circumference')
        self.assertIsNotNone(measure)


if __name__ == "__main__":
    unittest.main()
