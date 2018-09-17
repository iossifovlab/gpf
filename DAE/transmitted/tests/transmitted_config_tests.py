'''
Created on Oct 23, 2015

@author: lubo
'''
from __future__ import unicode_literals
import unittest
from DAE import vDB
from transmitted.base_query import TransmissionConfig


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.transmitted_study = vDB.get_study("w1202s766e611")
        cls.query = TransmissionConfig(cls.transmitted_study)

    def test_config_section(self):
        study = self.transmitted_study
        self.assertIsNotNone(study)
        self.assertIsNotNone(self.query)

    def test_default_call_set(self):
        self.assertIsNotNone(self.query._get_params("format"))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
