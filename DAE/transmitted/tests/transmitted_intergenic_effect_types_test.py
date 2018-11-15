'''
Created on Nov 3, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from transmitted.legacy_query import TransmissionLegacy
from transmitted.mysql_query import MysqlTransmittedQuery
import pytest


def count(vs):
    count = 0
    for _v in vs:
        count += 1
    return count


@pytest.mark.xfail
@pytest.mark.mysql
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.transmitted_study = vDB.get_study("w1202s766e611")
        cls.legacy = TransmissionLegacy(cls.transmitted_study, "old")
        cls.mysql = MysqlTransmittedQuery(cls.transmitted_study)

    request = {
        "minParentsCalled": 0,
        "maxAltFreqPrcnt": (-1),
        "minAltFreqPrcnt": (-1),
        "familyIds": ['11001'],
        "effectTypes": ['intergenic'],
    }

    def test_intergenic_legacy_query_len(self):
        lvs = self.legacy.get_transmitted_variants(**self.request)
        self.assertEquals(950, count(lvs))

    def test_intergenic_mysql_query_len(self):
        lvs = self.mysql.get_transmitted_variants(**self.request)
        self.assertEquals(950, count(lvs))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
