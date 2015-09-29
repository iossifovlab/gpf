'''
Created on Sep 24, 2015

@author: lubo
'''
import unittest
from transmitted.mysql_query import MysqlTransmittedQuery
from DAE import vDB
from query_prepare import prepare_gene_sets


class SummaryVariantsLenTest(unittest.TestCase):

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
        res = self.impl.get_transmitted_summary_variants(
            effectTypes=['missense'])
        self.assertEquals(589907, len(res))
        # print(res[0:30])

    def test_lgds_effect_type_len(self):
        self.impl.connect()
        lgds = list(vDB.effectTypesSet('LGDs'))
        res = self.impl.get_transmitted_summary_variants(
            effectTypes=lgds)
        self.assertEquals(36520, len(res))
        # print(res[0:30])

    def test_gene_syms_pogz_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            geneSyms=['POGZ'])
        self.assertEquals(153, len(res))

    def test_gene_syms_many1_len(self):
        gene_syms = ['SMARCC2', 'PGM2L1', 'SYNPO', 'ZCCHC14',
                     'CPE', 'HIPK3', 'HIPK2', 'HIPK1', 'GPM6A',
                     'TULP4', 'JPH4', 'FAM190B', 'FKBP8', 'KIAA0090']
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            geneSyms=gene_syms)
        self.assertEquals(1100, len(res))

    def test_gene_sym_gene_set(self):
        gene_syms = list(prepare_gene_sets({'geneSet': 'main',
                                            'geneTerm': 'FMR1-targets'}))
        assert gene_syms
        assert isinstance(gene_syms, list)

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            geneSyms=gene_syms)
        self.assertEquals(116195, len(res))

    def test_gene_sym_gene_set_lgds(self):
        gene_syms = list(prepare_gene_sets({'geneSet': 'main',
                                            'geneTerm': 'FMR1-targets'}))
        lgds = list(vDB.effectTypesSet('LGDs'))

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            geneSyms=gene_syms,
            effectTypes=lgds)
        self.assertEquals(850, len(res))

    def test_ultra_rare_lgds_len(self):
        lgds = list(vDB.effectTypesSet('LGDs'))

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            effectTypes=lgds,
            ultraRareOnly=True)
        self.assertEquals(28265, len(res))

    def test_ultra_rare_ins_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            variantTypes=['ins'],
            ultraRareOnly=True)
        self.assertEquals(13530, len(res))

    def test_all_ultra_rare_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            ultraRareOnly=True)
        self.assertEquals(867513, len(res))

    def test_ultra_rare_all_variant_types_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            variantTypes=['ins', 'del', 'sub'],
            ultraRareOnly=True)
        self.assertEquals(867513, len(res))

    def test_ultra_rare_single_region(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(32079, len(res))

    def test_ultra_rare_multiple_regions(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            ultraRareOnly=True,
            regionS=["1:0-60000000", "X:1000000-30000000"])

        self.assertEquals(36299, len(res))

    def test_region_matcher(self):
        res = self.impl._build_region_where("1:1-2")
        self.assertEquals(" ( tsv.chrome = '1' AND "
                          "tsv.position > 1 AND "
                          "tsv.position < 2 ) ",
                          res)
        res = self.impl._build_region_where("X:1-2")
        self.assertEquals(" ( tsv.chrome = 'X' "
                          "AND tsv.position > 1 "
                          "AND tsv.position < 2 ) ",
                          res)
        res = self.impl._build_region_where("Y:1-2")
        self.assertIsNone(res)
        res = self.impl._build_region_where("X:a-2")
        self.assertIsNone(res)

    def test_ultra_rare_single_region_lgds(self):
        lgds = list(vDB.effectTypesSet('LGDs'))

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            effectTypes=lgds,
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(1003, len(res))

#     def test_find_gene_syms_problem_len(self):
#         gene_syms = list(prepare_gene_sets({'geneSet': 'main',
#                                             'geneTerm': 'FMR1-targets'}))
#         st = vDB.get_study('w1202s766e611')
#         self.impl.connect()
#         problems = []
#         for sym in gene_syms:
#             vs = st.get_transmitted_summary_variants(geneSyms=[sym])
#             count = 0
#             for _v in vs:
#                 count += 1
#             res = self.impl.get_transmitted_summary_variants1(geneSyms=[sym])
#             if count != len(res):
#                 problems.append((count, len(res),
#                                  "gene sym: {}".format(sym)))
#         self.assertFalse(problems, "{}".format(problems))


class VariantsLenTest(unittest.TestCase):

    def setUp(self):
        self.impl = MysqlTransmittedQuery(vDB, 'w1202s766e611')

    def tearDown(self):
        self.impl.disconnect()

    def test_ultra_rare_single_region_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(32079, len(res))




if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
