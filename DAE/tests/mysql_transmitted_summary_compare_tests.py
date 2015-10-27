'''
Created on Oct 27, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery


class Test(unittest.TestCase):

    def setUp(self):
        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

    def tearDown(self):
        self.impl.disconnect()

    def test_synonymous_background(self):
        pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
