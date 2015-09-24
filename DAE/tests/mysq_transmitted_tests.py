'''
Created on Sep 24, 2015

@author: lubo
'''
import unittest
from transmitted.mysql_query import MysqlTransmittedQuery
from DAE import vDB


class Test(unittest.TestCase):

    def setUp(self):
        self.impl = MysqlTransmittedQuery(vDB, 'w1202s766e611')

    def tearDown(self):
        self.impl.disconnect()

    def test_mysql_query_object_created(self):
        self.assertIsNotNone(self.impl)

    def test_has_default_query(self):
        self.assertIsNotNone(self.impl)
        self.assertIn('minParentsCalled', self.impl.query)
        self.assertIn('maxAltFreqPrcnt', self.impl.query)

    def test_connect(self):
        self.impl.connect()
        self.assertIsNotNone(self.impl.connection)

    def test_default_freq_query(self):
        where = self.impl._build_freq_where()
        self.assertIsNotNone(where)
        self.assertEquals(' ( tsv.n_par_called > 600 ) '
                          ' AND  ( tsv.alt_freq <= 5.0 ) ',
                          where)

    def test_default_query_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants()
        # 1350367
        self.assertEquals(1350367, len(res))

    def test_missense_effect_type_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants1(
            effectTypes=['missense'])
        self.assertEquals(589907, len(res))
        # print(res[0:30])

    def test_lgds_effect_type_len(self):
        self.impl.connect()
        lgds = list(vDB.effectTypesSet('LGDs'))
        res = self.impl.get_transmitted_summary_variants1(
            effectTypes=lgds)
        self.assertEquals(36520, len(res))
        # print(res[0:30])


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
