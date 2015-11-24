'''
Created on Nov 24, 2015

@author: lubo
'''
import os
import unittest
import pandas as pd


class Test(unittest.TestCase):
    FILENAME = os.path.join(os.path.dirname(__file__), "phnGnt.csv")

    def setUp(self):
        self.df = pd.read_csv(self.FILENAME)

    def tearDown(self):
        pass

    def test_df_not_none(self):
        self.assertIsNotNone(self.df)


if __name__ == "__main__":
    unittest.main()
