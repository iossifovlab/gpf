'''
Created on Aug 10, 2016

@author: lubo
'''
import unittest
from pheno_db.utils.load_raw import V14Loader


class V14LoaderTest(unittest.TestCase):

    def setUp(self):
        self.loader = V14Loader()

    def tearDown(self):
        pass

    def test_config(self):
        self.assertIsNotNone(self.loader.v14)
        self.assertIsNotNone(self.loader.v15)

    def test_v14_load_main(self):
        df = self.loader.load_main()
        self.assertIsNotNone(df)

    def test_v14_load_cdv(self):
        df = self.loader.load_cdv()
        self.assertIsNotNone(df)

    def test_check_cdv_categories(self):
        df = self.loader.load_cdv()
        df1 = self.loader._load_df(self.loader.CDV_OLD)

        self.assertIsNotNone(df1)
        self.assertEquals(len(df1), len(df))
        self.assertTrue((df.variableCategory == df1.variableCategory).all())

    def test_v14_load_ocuv(self):
        df = self.loader.load_ocuv()
        self.assertIsNotNone(df)

    def test_load_everything(self):
        df = self.loader.load_everything()
        self.assertIsNotNone(df)

if __name__ == "__main__":
    unittest.main()
