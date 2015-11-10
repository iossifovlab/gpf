'''
Created on Sep 24, 2015

@author: lubo
'''
import unittest
from transmitted.mysql_query import MysqlTransmittedQuery
from DAE import vDB, get_gene_sets_symNS


def count(vs):
    l = 0
    for _ in vs:
        l += 1
    return l


def get_gene_set_syms(gene_set, gene_term):
    gt = get_gene_sets_symNS(gene_set)
    if gt and gene_term in gt.t2G:
        return gt.t2G[gene_term].keys()


class SummaryVariantsLenTest(unittest.TestCase):

    def setUp(self):
        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

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
        self.assertEquals(' ( tsv.alt_freq <= 5.0 ) ',
                          where)

    def test_default_query_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600)
        # 1350367
        self.assertEquals(1350367, count(res))

    def test_missense_effect_type_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            effectTypes=['missense'])
        self.assertEquals(589907, count(res))
        # print(res[0:30])

    def test_lgds_effect_type_len(self):
        self.impl.connect()
        lgds = list(vDB.effectTypesSet('LGDs'))
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            effectTypes=lgds)
        self.assertEquals(36520, count(res))
        # print(res[0:30])

    def test_gene_syms_pogz_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            geneSyms=['POGZ'])
        self.assertEquals(153, count(res))

    def test_gene_syms_many1_len(self):
        gene_syms = ['SMARCC2', 'PGM2L1', 'SYNPO', 'ZCCHC14',
                     'CPE', 'HIPK3', 'HIPK2', 'HIPK1', 'GPM6A',
                     'TULP4', 'JPH4', 'FAM190B', 'FKBP8', 'KIAA0090']
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            geneSyms=gene_syms)
        self.assertEquals(1100, count(res))

    def test_gene_sym_gene_set(self):

        gene_syms = get_gene_set_syms('main', 'FMR1-targets')
        assert gene_syms
        assert isinstance(gene_syms, list)

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            geneSyms=gene_syms)
        self.assertEquals(116195, count(res))

    def test_gene_sym_gene_set_lgds(self):
        gene_syms = get_gene_set_syms('main', 'FMR1-targets')
        lgds = list(vDB.effectTypesSet('LGDs'))

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            geneSyms=gene_syms,
            effectTypes=lgds)
        self.assertEquals(850, count(res))

    def test_ultra_rare_lgds_len(self):
        lgds = list(vDB.effectTypesSet('LGDs'))

        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            effectTypes=lgds,
            ultraRareOnly=True)
        self.assertEquals(28265, count(res))

    def test_ultra_rare_ins_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            variantTypes=['ins'],
            ultraRareOnly=True)
        self.assertEquals(13530, count(res))

    def test_all_ultra_rare_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            ultraRareOnly=True)
        self.assertEquals(867513, count(res))

    def test_ultra_rare_all_variant_types_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            variantTypes=['ins', 'del', 'sub'],
            ultraRareOnly=True)
        self.assertEquals(867513, count(res))

    def test_ultra_rare_single_region(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(32079, count(res))

    def test_ultra_rare_multiple_regions(self):
        self.impl.connect()
        res = self.impl.get_transmitted_summary_variants(
            minParentsCalled=600,
            ultraRareOnly=True,
            regionS=["1:0-60000000", "X:1000000-30000000"])

        self.assertEquals(36299, count(res))

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
            minParentsCalled=600,
            effectTypes=lgds,
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(1003, count(res))


class VariantsLenTest(unittest.TestCase):

    def setUp(self):
        transmitted_study = vDB.get_study("w1202s766e611")
        self.impl = MysqlTransmittedQuery(transmitted_study)

    def tearDown(self):
        self.impl.disconnect()

    def test_ultra_rare_single_region_len(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=600,
            ultraRareOnly=True,
            regionS=["1:0-60000000"])

        self.assertEquals(32079, count(res))

    def test_variants_in_single_family_id(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=600,
            familyIds=["11110"])

        self.assertEquals(5701, count(res))

    def test_variants_in_two_family_ids(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=600,
            familyIds=["11110", "11111"])

        self.assertEquals(9322, count(res))

    #  get_variants.py --denovoStudies=none --effectTypes=none
    # --transmittedStudy=w1202s766e611 --popMinParentsCalled=-1
    # --popFrequencyMax=-1 --familiesList=13785
    def test_all_variants_in_single_family_id(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=None,
            maxAltFreqPrcnt=None,
            familyIds=["13785"])
        self.assertEquals(29375, count(res))

    def test_family_id_and_pogz(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=600,
            familyIds=['13983'],
            geneSyms=['POGZ'])

        self.assertEquals(1, count(res))

    def test_family_id_and_pogz_all(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            familyIds=['13983'],
            geneSyms=['POGZ'],
            minParentsCalled=None,
            maxAltFreqPrcnt=None)

        self.assertEquals(3, count(res))

    def test_family_id_and_pogz_effect_types(self):
        res = self.impl.get_transmitted_variants(
            familyIds=['13983'],
            geneSyms=['POGZ'],
            effectTypes=["frame-shift", "intergenic", "intron", "missense",
                         "non-coding", "no-frame-shift", "nonsense",
                         "splice-site", "synonymous", "noEnd", "noStart",
                         "3'UTR", "5'UTR", "CNV+", "CNV-"],
            minParentsCalled=None,
            maxAltFreqPrcnt=None)

        self.assertEquals(3, count(res))

    def test_family_id_and_pogz_effect_types_case_insensitive(self):
        res = self.impl.get_transmitted_variants(
            familyIds=['13983'],
            geneSyms=['pogz'],
            effectTypes=["frame-shift", "intergenic", "intron", "missense",
                         "non-coding", "no-frame-shift", "nonsense",
                         "splice-site", "synonymous", "noEnd", "noStart",
                         "3'UTR", "5'UTR", "CNV+", "CNV-"],
            minParentsCalled=None,
            maxAltFreqPrcnt=None)

        self.assertEquals(3, count(res))


class VariantsFullTest(unittest.TestCase):

    def setUp(self):
        self.st = vDB.get_study('w1202s766e611')
        self.impl = MysqlTransmittedQuery(self.st)

    def tearDown(self):
        self.impl.disconnect()

    def test_family_id_and_pogz(self):
        self.impl.connect()
        res = self.impl.get_transmitted_variants(
            minParentsCalled=600,
            familyIds=['13983'],
            geneSyms=['POGZ'])
        vs = self.st.get_transmitted_variants(
            minParentsCalled=600,
            familyIds=['13983'],
            geneSyms=['POGZ'])
        v = vs.next()
        r = res.next()
        self.assertIsNotNone(v)
        self.assertIsNotNone(r)
        self.assertEquals(v.location, r.location)


class VariantsPresentInParentTest(unittest.TestCase):

    def setUp(self):
        self.st = vDB.get_study('w1202s766e611')
        self.impl = MysqlTransmittedQuery(self.st)

    def tearDown(self):
        self.impl.disconnect()

    def test_present_in_parent_all(self):
        request = {
            "geneSyms": ["JAKMIP1", "OR4C11", "OSBPL",
                         "OTUD4", "PAX5", "PHF21A", "WRAP73", "VWA5B1"],
            "effectTypes": ["nonsense", "frame-shift", "splice-site"],
            "presentInParent": ["mother only", "father only",
                                "mother and father", "neither"],
            "ultraRareOnly": True,
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(14, count(res))

    def test_present_in_parent_father_only(self):
        request = {
            "geneSyms": ["JAKMIP1", "OR4C11", "OSBPL",
                         "OTUD4", "PAX5", "PHF21A", "WRAP73", "VWA5B1"],
            "effectTypes": ["nonsense", "frame-shift", "splice-site"],
            "presentInParent": ["father only", ],
            "ultraRareOnly": True,
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(9, count(res))

    def test_present_in_parent_mother_only(self):
        request = {
            "geneSyms": ["JAKMIP1", "OR4C11", "OSBPL",
                         "OTUD4", "PAX5", "PHF21A", "WRAP73", "VWA5B1"],
            "effectTypes": ["nonsense", "frame-shift", "splice-site"],
            "presentInParent": ["mother only", ],
            "ultraRareOnly": True,
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(5, count(res))

    def test_present_in_parent_mother_only_or_father_only(self):
        request = {
            "geneSyms": ["JAKMIP1", "OR4C11", "OSBPL",
                         "OTUD4", "PAX5", "PHF21A", "WRAP73", "VWA5B1"],
            "effectTypes": ["nonsense", "frame-shift", "splice-site"],
            "presentInParent": ["mother only", "father only"],
            "ultraRareOnly": True,
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(14, count(res))

    def test_present_in_parent_mother_and_father(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(82, count(res))

    def test_present_in_parent_neither(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["neither"],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(0, count(res))


class VariantsPresentInChildTest(unittest.TestCase):

    def setUp(self):
        self.st = vDB.get_study('w1202s766e611')
        self.impl = MysqlTransmittedQuery(self.st)

    def tearDown(self):
        self.impl.disconnect()

    def test_present_in_child_all(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism only", "unaffected only",
                               "autism and unaffected", "neither", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(82, count(res))

    def test_present_in_child_autism_and_unaffected(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism and unaffected", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(40, count(res))

    def test_present_in_child_neither(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["neither", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(6, count(res))

    def test_present_in_autism_only(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism only", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(28, count(res))

    def test_present_in_unaffected_only(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["unaffected only", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(8, count(res))

    def test_present_in_autism_and_unaffected(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism and unaffected", ],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(40, count(res))

    def test_present_in_autism_only_female(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism only", ],
            'gender': ['F'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(6, count(res))

    def test_present_in_autism_only_male(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism only", ],
            'gender': ['M'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(22, count(res))

    def test_present_in_unaffected_only_female(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["unaffected only", ],
            'gender': ['F'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(4, count(res))

    def test_present_in_unaffected_only_male(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["unaffected only", ],
            'gender': ['M'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(4, count(res))

    def test_present_in_autism_and_unaffected_female(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism and unaffected", ],
            'gender': ['F'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(27, count(res))

    def test_present_in_autism_and_unaffected_male(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism and unaffected", ],
            'gender': ['M'],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(38, count(res))


class VariantsInChildTest(unittest.TestCase):

    def setUp(self):
        self.st = vDB.get_study('w1202s766e611')
        self.impl = MysqlTransmittedQuery(self.st)

    def tearDown(self):
        self.impl.disconnect()

    def test_in_child_prb(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "prb",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(68, count(res))

    def test_present_in_child_prb(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["autism only", "autism and unaffected"],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(68, count(res))

    def test_in_child_prb_male(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "prbM",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(57, count(res))

    def test_in_child_prb_female(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "prbF",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(11, count(res))

    def test_in_child_sib(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "sib",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(48, count(res))

    def test_in_child_sib_male(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "sibM",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(20, count(res))

    def test_in_child_sib_female(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "inChild": "sibF",
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(28, count(res))

    def test_present_in_child_sib(self):
        request = {
            "geneSyms": ["SCNN1D"],
            "effectTypes": ['missense'],
            "presentInParent": ["mother and father"],
            "presentInChild": ["unaffected only", "autism and unaffected"],
            "minParentsCalled": 600,
        }
        self.impl.connect()
        res = self.impl.get_transmitted_variants(**request)
        self.assertEquals(48, count(res))


#     def test_present_in_child_autism_and_unaffected(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism and unaffected", ]
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(40, count(res))
#
#     def test_present_in_child_neither(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["neither", ]
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(6, count(res))
#
#     def test_present_in_autism_only(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism only", ]
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(28, count(res))
#
#     def test_present_in_unaffected_only(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["unaffected only", ]
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(8, count(res))
#
#     def test_present_in_autism_and_unaffected(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism and unaffected", ]
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(40, count(res))
#
#     def test_present_in_autism_only_female(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism only", ],
#             'gender': ['F'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(6, count(res))
#
#     def test_present_in_autism_only_male(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism only", ],
#             'gender': ['M'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(22, count(res))
#
#     def test_present_in_unaffected_only_female(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["unaffected only", ],
#             'gender': ['F'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(4, count(res))
#
#     def test_present_in_unaffected_only_male(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["unaffected only", ],
#             'gender': ['M'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(4, count(res))
#
#     def test_present_in_autism_and_unaffected_female(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism and unaffected", ],
#             'gender': ['F'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(27, count(res))
#
#     def test_present_in_autism_and_unaffected_male(self):
#         request = {
#             "geneSyms": ["SCNN1D"],
#             "effectTypes": ['missense'],
#             "presentInParent": ["mother and father"],
#             "presentInChild": ["autism and unaffected", ],
#             'gender': ['M'],
#         }
#         self.impl.connect()
#         res = self.impl.get_transmitted_variants(**request)
#         self.assertEquals(38, count(res))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
