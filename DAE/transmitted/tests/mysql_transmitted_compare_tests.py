'''
Created on Oct 15, 2015

@author: lubo
'''
from __future__ import unicode_literals
from transmitted.tests.variants_compare_base import VariantsCompareBase
from transmitted.tests.mysql_transmitted_std_queries import dae_query_q101,\
    mysql_query_q101, dae_query_q201, mysql_query_q201, dae_query_q301,\
    mysql_query_q301, dae_query_q401, mysql_query_q401, dae_query_q501,\
    mysql_query_q501, dae_query_q601, mysql_query_q601, dae_query_q701,\
    mysql_query_q701, dae_query_q801, mysql_query_q801


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

    def test_compare_q701(self):
        dae_res = dae_query_q701()
        mysql_res = mysql_query_q701()

        self.assertVariantsEquals(dae_res, mysql_res, 'q701')

    def test_compare_q801(self):
        dae_res = dae_query_q801()
        mysql_res = mysql_query_q801()

        self.assertVariantsEquals(dae_res, mysql_res, 'q801')
