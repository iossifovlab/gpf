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

    @unittest.skip
    def test_synonymous_background(self):
        transmitted_study = vDB.get_study('w1202s766e611')
        ovs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"],
                    callSet='old')
        mvs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"])
        ores = [v for v in ovs]
        mres = [v for v in mvs]

        self.assertSummaryVariantsEquals(mres, ores, 'synonymous background')

    def test_summary_variants_gene_sym_MAGEA12(self):
        transmitted_study = vDB.get_study('w1202s766e611')
        ovs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"],
                    geneSyms=["MAGEA12"],
                    callSet='old')
        mvs = transmitted_study.get_transmitted_summary_variants(
                    ultraRareOnly=True,
                    minParentsCalled=600,
                    effectTypes=["synonymous"],
                    geneSyms=["MAGEA12"])

        ores = [v for v in ovs]
        mres = [v for v in mvs]

        self.assertTrue(len(ores) > 0, "variants not found...")

        self.assertSummaryVariantsEquals(mres, ores, 'MAGEA12')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
