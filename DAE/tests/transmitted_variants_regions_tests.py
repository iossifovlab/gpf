'''
Created on Oct 26, 2015

@author: lubo
'''
import unittest
from query_variants import prepare_transmitted_filters, \
    prepare_denovo_filters, \
    validate_region
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery


class ValidateRegionsTest(unittest.TestCase):

    def test_validate_region(self):
        self.assertTrue(validate_region("1:86874300-86874400"))


class QueryTest(unittest.TestCase):

    def setUp(self):
        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

    def test_region(self):
        request = {
            "effectTypes": "All",
            "families": "All",
            "gender": "female,male",
            "geneRegion": "1:86874300-86874400",
            "presentInChild": "autism only",
            "presentInParent":
            "father only,mother and father,mother only,neither",
            "variantTypes": "CNV,del,ins,sub",
            "genes": "All",
            "rarity": "ultraRare",
            'transmittedStudies': 'w1202s766e611'
            }
        params = prepare_denovo_filters(request)
        params = prepare_transmitted_filters(request, params)
        vs = self.impl.get_transmitted_variants(**params)
        count = 0
        for v in vs:
            count += 1
            self.assertTrue(int(v.position) >= 86874300)
            self.assertTrue(int(v.position) <= 86874400)
            self.assertEquals("1", v.chr)
        self.assertTrue(count > 0)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
