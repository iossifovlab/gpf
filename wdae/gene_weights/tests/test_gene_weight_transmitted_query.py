'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from preloaded.register import get_register
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery


def count(vs):
    l = 0
    for _ in vs:
        l += 1
    return l


class Test(unittest.TestCase):

    def setUp(self):
        register = get_register()
        self.weights = register.get('gene_weights')

        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

    def tearDown(self):
        pass

    def test_weights_are_not_none(self):
        self.assertIsNotNone(self.weights)

    def test_query_all_rvis_genes(self):
        genes = self.weights.get_genes_by_weight('RVIS_rank', wmin=None, wmax=None)
        self.assertEqual(16642, len(genes))

        res = self.impl.get_transmitted_variants(
            ultraRareOnly=True,
            geneSyms=genes,
            limit=1000)

        self.assertEqual(1000, count(res))

#     def test_query_all_lgd_and_rvis_rank(self):
#         genes = self.weights.get_genes_by_weight(
#             'LGD_and_RVIS_average_rank',
#             wmin=None, wmax=None)
#         self.assertEqual(16642, len(genes))
# 
#         res = self.impl.get_transmitted_variants(
#             ultraRareOnly=True,
#             geneSyms=genes,
#             limit=1000)
# 
#         self.assertEqual(1000, count(res))


if __name__ == "__main__":
    unittest.main()
