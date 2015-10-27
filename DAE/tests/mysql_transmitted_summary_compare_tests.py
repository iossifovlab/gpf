'''
Created on Oct 27, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery
from variants_compare_base import VariantsCompareBase


class Test(VariantsCompareBase):

    def setUp(self):
        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

    def tearDown(self):
        self.impl.disconnect()

    def test_synonymous_background(self):
        transmitted_study = vDB.get_study('w1202s766e611')
        vs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"], callSet='old')
        nvs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"], callSet='old')
        vres = [v for v in vs]
        nvres = [v for v in nvs]

        self.assertSummaryVariantsEquals(vres, nvres, 'synonymous background')
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
