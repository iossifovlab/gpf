'''
Created on Oct 15, 2015

@author: lubo
'''
import unittest
from mysql_transmitted_std_queries import dae_query_q101, mysql_query_q101
from mysql_transmitted_std_queries import dae_query_q201, mysql_query_q201
from mysql_transmitted_std_queries import dae_query_q301, mysql_query_q301
from mysql_transmitted_std_queries import dae_query_q401, mysql_query_q401
from mysql_transmitted_std_queries import dae_query_q501, mysql_query_q501
from mysql_transmitted_std_queries import dae_query_q601, mysql_query_q601
from variants_compare_base import VariantsCompareBase


class Test(VariantsCompareBase):

    def test_compare_q101(self):
        dae_res = dae_query_q101()
        mysql_res = mysql_query_q101()

        self.assertVariantsEquals(dae_res, mysql_res, 'q101')

    def test_compare_q201(self):
        dae_res = dae_query_q201()
        mysql_res = mysql_query_q201()

        self.assertVariantsEquals(dae_res, mysql_res, 'q201')

    def test_compare_q301(self):
        dae_res = dae_query_q301()
        mysql_res = mysql_query_q301()

        self.assertVariantsEquals(dae_res, mysql_res, 'q301')

    def test_compare_q401(self):
        dae_res = dae_query_q401()
        mysql_res = mysql_query_q401()

        self.assertVariantsEquals(dae_res, mysql_res, 'q401')

    def test_compare_q501(self):
        dae_res = dae_query_q501()
        mysql_res = mysql_query_q501()

        self.assertVariantsEquals(dae_res, mysql_res, 'q501')

    def test_compare_q601(self):
        dae_res = dae_query_q601()
        mysql_res = mysql_query_q601()

        self.assertVariantsEquals(dae_res, mysql_res, 'q601')

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
