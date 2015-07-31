'''
Created on Jul 31, 2015

@author: lubo
'''
import unittest
from api.reports.variants import VariantReports


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.vr = VariantReports()
        cls.vr.precompute()
        cls.data = cls.vr.serialize()

    def setUp(self):
        self.vr = VariantReports()
        self.vr.deserialize(self.data)

    def tearDown(self):
        pass

    def test_serialize_deserialize_not_none(self):
        self.assertIsNotNone(self.data)

    def test_deserialize(self):
        self.assertIsNotNone(self.vr.data)

    def test_deserialize_all_we_study(self):
        sr = self.vr['ALL WHOLE EXOME']
        self.assertIsNotNone(sr)
        self.assertIsNotNone(sr.families_report)
        self.assertIsNotNone(sr.denovo_report)

    def test_deserialize_lifton_study(self):
        sr = self.vr['Lifton2013CHD']
        self.assertIsNotNone(sr)
        self.assertIsNotNone(sr.families_report)
        self.assertIsNotNone(sr.denovo_report)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_']
    unittest.main()
