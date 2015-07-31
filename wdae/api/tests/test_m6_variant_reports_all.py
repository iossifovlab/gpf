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

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_serialize_deserialize(self):
        data = self.vr.serialize()
        self.assertIsNotNone(data)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_']
    unittest.main()
