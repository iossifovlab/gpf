import unittest

from api.dae_query import prepare_inchild, prepare_effect_types, \
    prepare_variant_types, prepare_family_ids, prepare_gene_syms, \
    prepare_gene_sets, prepare_denovo_studies, \
    prepare_transmitted_studies, dae_query_variants, \
    do_query_variants

import logging
import itertools

logger = logging.getLogger(__name__)


class FamilesTests(unittest.TestCase):

    def test_families_empty(self):
        self.assertIsNone(prepare_family_ids({}))

    def test_families_none(self):
        self.assertIsNone(prepare_family_ids({'familyIds': 'None'}))
        self.assertIsNone(prepare_family_ids({'familyIds': 'none'}))
        self.assertIsNone(prepare_family_ids({'familyIds': 'All'}))
        self.assertIsNone(prepare_family_ids({'familyIds': 'all'}))
        self.assertIsNone(prepare_family_ids({'familyIds': None}))
        self.assertIsNone(prepare_family_ids({'familyIds': 15}))

    def test_families_string(self):
        self.assertListEqual(
            prepare_family_ids({'familyIds': '111'}),
            ['111'])
        self.assertListEqual(
            prepare_family_ids({'familyIds': '111,222'}),
            ['111', '222'])
        self.assertListEqual(
            prepare_family_ids({'familyIds': '111 , 222'}),
            ['111', '222'])
        self.assertListEqual(
            prepare_family_ids({'familyIds': '111    ,    222'}),
            ['111', '222'])
        self.assertListEqual(
            prepare_family_ids({'familyIds': '111     ,    222,'}),
            ['111', '222'])

    def test_families_list(self):
        self.assertListEqual(
            prepare_family_ids({'familyIds': ['111']}),
            ['111'])
        self.assertListEqual(
            prepare_family_ids({'familyIds': ['111', '222']}),
            ['111', '222'])


class GeneSymsTests(unittest.TestCase):

    def test_gen_syms_empty(self):
        self.assertIsNone(prepare_gene_syms({}))

    def test_gen_syms_none(self):
        self.assertIsNone(prepare_gene_syms({'geneSyms': ''}))
        self.assertIsNone(prepare_gene_syms({'geneSyms': '    '}))
        self.assertIsNone(prepare_gene_syms({'geneSyms': None}))

    def test_gen_syms_correct_string(self):
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': 'CDH1'}),
            set(['CDH1']))
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': 'CDH1,SCO2'}),
            set(['CDH1', 'SCO2']))
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': 'CDH1      ,      SCO2'}),
            set(['CDH1', 'SCO2']))
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': 'CDH1      ,      SCO2  ,   '}),
            set(['CDH1', 'SCO2']))

    # No gene sym filtering!!!
    # def test_gen_syms_not_correct_string(self):
    #     self.assertIsNone(
    #         prepare_gene_syms({'geneSyms': 'ala-bala'}))
    #     self.assertSetEqual(
    #         prepare_gene_syms({'geneSyms': 'CDH1,ala-bala'}), set(['CDH1']))

    def test_gen_syms_correct_list(self):
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': ['CDH1']}),
            set(['CDH1']))
        self.assertSetEqual(
            prepare_gene_syms({'geneSyms': ['CDH1', 'SCO2']}),
            set(['CDH1', 'SCO2']))

    # No gene symbols filtering...
    # def test_gen_syms_not_correct_list(self):
    #     self.assertIsNone(
    #         prepare_gene_syms({'geneSyms': ['ala-bala']}))
    #     self.assertSetEqual(
    #         prepare_gene_syms({'geneSyms': ['ala-bala', 'SCO2']}),
    #         set(['SCO2']))


class GeneSetsTests(unittest.TestCase):
    DISEASE_AIDS = set(['IFNG', 'KIR3DL1', 'CXCL12'])
    GO_GO_2001293 = set(['ACACA', 'ACACB'])
    MAIN_mPFC_maternal = set(['RAD23B', 'ADD2', 'NCOR2', 'CERS4',
                              'PPP1R3C', 'KCNK9', 'CLIP2', 'ARF3',
                              'ADAR', 'DEF8', 'SLC4A8', 'RFTN2',
                              'COPG2', 'LDHD', 'SPTLC2', 'KCTD20',
                              'NNT', 'IGF2', 'CLCN2', 'UBE2E2',
                              'HERC3', 'MEG3', 'TOB1', 'UBR4',
                              'ZNF157', 'AKAP2', 'DOPEY2', 'SCN1B',
                              'LIMCH1'])

    def test_gene_sets_empty(self):
        self.assertIsNone(prepare_gene_sets({}))

    def test_gete_sets_main(self):
        gs = prepare_gene_sets({'geneSet':
                                {'gs_id':'main', 'gs_term':'mPFC_maternal'}})
        self.assertSetEqual(gs, self.MAIN_mPFC_maternal)
        self.assertTrue(isinstance(gs, set))

    def test_gete_sets_go(self):
        gs = prepare_gene_sets({'geneSet':
                                {'gs_id': 'GO', 'gs_term': 'GO:2001293'}})
        self.assertSetEqual(gs, self.GO_GO_2001293)
        self.assertTrue(isinstance(gs, set))

    def test_gete_sets_disease(self):
        gs = prepare_gene_sets({'geneSet':
                                {'gs_id': 'disease', 'gs_term': 'AIDS'}})
        self.assertSetEqual(gs, self.DISEASE_AIDS)
        self.assertTrue(isinstance(gs, set))


class StudiesTests(unittest.TestCase):

    def test_denovo_studies_empty(self):
        dsl = prepare_denovo_studies({'denovoStudies': []})
        self.assertIsNone(dsl)

        dsl = prepare_denovo_studies({})
        self.assertIsNone(dsl)

    def test_denovo_studies_single(self):
        dsl = prepare_denovo_studies({'denovoStudies': ["DalyWE2012"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "DalyWE2012")

        dsl = prepare_denovo_studies({'denovoStudies': ["EichlerTG2012"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "EichlerTG2012")

    def test_denovo_studies_double(self):
        dsl = prepare_denovo_studies({'denovoStudies':
                                      ["DalyWE2012", "EichlerTG2012"]})
        self.assertEquals(len(dsl), 2)

        self.assertEqual(dsl[0].name, "DalyWE2012")
        self.assertEqual(dsl[1].name, "EichlerTG2012")

    def test_denovo_studies_not_found(self):
        dsl = prepare_denovo_studies({'denovoStudies': ["ala", "bala"]})
        self.assertIsNone(dsl)

    def test_transmitted_studies_empty(self):
        dsl = prepare_transmitted_studies({'transmittedStudies': []})
        self.assertIsNone(dsl)

        dsl = prepare_transmitted_studies({})
        self.assertIsNone(dsl)

    def test_transmitted_studies_single(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':
                                           ["w873e374s322"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "w873e374s322")

        dsl = prepare_transmitted_studies({'transmittedStudies':
                                           ["wig683"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "wig683")

    def test_transmitted_studies_double(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':
                                           ["w873e374s322", "wig683"]})
        self.assertEquals(len(dsl), 2)

        self.assertEqual(dsl[0].name, "w873e374s322")
        self.assertEqual(dsl[1].name, "wig683")

    def test_transmitted_studies_not_found(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':
                                           ["ala", "bala"]})
        self.assertIsNone(dsl)


class VariantsTests(unittest.TestCase):

    def test_studies_empty(self):
        vs = dae_query_variants({'denovoStudies': [],
                                 'transmittedStudies': []})
        self.assertListEqual(vs, [])

        vs = dae_query_variants({})
        self.assertListEqual(vs, [])

    def test_studies_single(self):
        vs = dae_query_variants({'denovoStudies': ["DalyWE2012"]})
        self.assertEqual(len(vs), 1)

        vs = dae_query_variants({'transmittedStudies': ["wig683"]})
        self.assertEqual(len(vs), 1)

#     def test_effect_type(self):
#         vs = dae_query_variants({'denovoStudies':["DalyWE2012"],
#                                  'transmittedStudies':["wig683"],
#                                  'effectTypes':'nonsense'})
#         self.assertEqual(len(vs),2)
#         for v in itertools.chain(*vs):
#             self.assertEqual(v.atts['effectType'],'nonsense')

    def test_variant_filters(self):
        vs = dae_query_variants({"denovoStudies": ["DalyWE2012"],
                                 "transmittedStudies": ["wig683"],
                                 "inChild": "sibF",
                                 "effectTypes": "frame-shift",
                                 "variantTypes": "del",
                                 "ultraRareOnly": "True"})

        self.assertEqual(len(vs), 2)
        for v in itertools.chain(*vs):
            self.assertTrue('sibF' in v.inChS)
            self.assertEqual(v.atts['effectType'], 'frame-shift')


class CombinedTests(unittest.TestCase):

    TEST_DATA_2 = {"denovoStudies": [],
                   "transmittedStudies": ["w873e374s322"],
                   "inChild": "prbF",
                   "effectTypes": "LoF",
                   "variantTypes": "All",
                   "geneSet": {"gs_id": "GO", "gs_term": "GO:0022889"},
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild(self.TEST_DATA_1), 'prbM')

    def test_gene_sets_main(self):
        gs = prepare_gene_sets(self.TEST_DATA_1)
        self.assertTrue(isinstance(gs, set))
        # self.assertEqual(len(gs), 1747)

    TEST_DATA_1 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": ["none"],
                   "inChild": "prbM",
                   "effectTypes": "frame-shift",
                   "variantTypes": "ins",
                   "geneSet": {"gs_id": "main", "gs_term": "essentialGenes"},
                   "geneSyms": ""}

    def test_variants_gene_sets_1(self):
        vs = do_query_variants(self.TEST_DATA_1)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        count = 0
        for v in vs:
            count += 1
            self.assertTrue('ins' in v[3], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbM' in v[6])
            self.assertTrue('frame-shift' in v[8])
            self.assertTrue('frame-shift' in v[9])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('prbM' in v[17])

        self.assertTrue(count > 0)
    # def test_variants_gene_sets_1_tmp(self):
    #     vs = dae_query_variants(self.TEST_DATA_1)

    #     self.assertEqual(len(vs), 1)
    #     tf = open("test_data_1.tmp", "w+")

    #     save_vs(tf, itertools.imap(augmentAVar, itertools.chain(*vs)),
    #             ['effectType',
    #              'effectDetails',
    #              'all.altFreq',
    #              'all.nAltAlls',
    #              'all.nParCalled',
    #              '_par_races_',
    #              '_ch_prof_'])

    #     tf.close()

    TEST_DATA_3 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": ["wigEichler374"],
                   "inChild": "prbF",
                   "effectTypes": "frame-shift",
                   "variantTypes": "del",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_variants_gene_sets_3(self):
        vs = do_query_variants(self.TEST_DATA_3)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertTrue('del' in v[3], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbF' in v[6])
            self.assertTrue('frame-shift' in v[8])
            self.assertTrue('frame-shift' in v[9])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('prbF' in v[17])

        # vs = dae_query_variants(self.TEST_DATA_3)

        # self.assertEqual(len(vs), 2)
        # tf = open("test_data_3.tmp", "w+")

        # save_vs(tf, itertools.imap(augmentAVar, itertools.chain(*vs)),
        #         ['effectType',
        #          'effectDetails',
        #          'all.altFreq',
        #          'all.nAltAlls',
        #          'all.nParCalled',
        #          '_par_races_',
        #          '_ch_prof_'])

        # tf.close()


class GeneRegionCombinedTests(unittest.TestCase):
    TEST_DATA = {"denovoStudies": [],
                 "transmittedStudies": ["wigEichler374"],
                 "inChild": "All",
                 "effectTypes": "All",
                 "variantTypes": "All",
                 "geneSet": None,
                 "geneRegion": "1:1018000-1020000",
                 "geneSyms": "",
                 "ultraRareOnly": True}

    def test_gene_region_filter(self):
        vs = do_query_variants(self.TEST_DATA)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            loc = int(v[2].split(':')[1])
            self.assertTrue(loc >= 1018000, "%s: %s" % (str(loc), str(v[2])))
            self.assertTrue(loc <= 1020000, "%s: %s" % (str(loc), str(v[2])))

        # vs = dae_query_variants(self.TEST_DATA_4)

        # self.assertEqual(len(vs), 1)
        # tf = open("test_data_4.tmp", "w+")

        # save_vs(tf, itertools.imap(augmentAVar, itertools.chain(*vs)),
        #         ['effectType',
        #          'effectDetails',
        #          'all.altFreq',
        #          'all.nAltAlls',
        #          'all.nParCalled',
        #          '_par_races_',
        #          '_ch_prof_'])

        # tf.close()


class QueryDictTests(unittest.TestCase):
    TEST_DATA_1 = "geneSymbols=&geneSet=main&geneSetInput=&denovoStudies=allWEAndTG&transmittedStudies=none&rarity=ultraRare&inChild=prb&variants=All&effectType=All&families="


class AdvancedFamilyFilterTests(unittest.TestCase):
    TEST_DATA_1 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyRace": 'african-amer'}

    def test_family_race(self):
        vs = do_query_variants(self.TEST_DATA_1)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertIn('african-amer', v[16])

    TEST_DATA_2 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyQuadTrio": 'Quad'}

    def test_family_quad(self):
        vs = do_query_variants(self.TEST_DATA_2)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertEqual(4, len(v[4].split('/')[0].split(' ')), str(v[4]))

    TEST_DATA_3 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyQuadTrio": 'Trio'}

    def test_family_trio(self):
        vs = do_query_variants(self.TEST_DATA_3)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertEqual(3, len(v[4].split('/')[0].split(' ')), str(v[4]))

    TEST_DATA_4 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familySibGender": 'female'}

    def test_family_sibling_gender_female(self):
        vs = do_query_variants(self.TEST_DATA_4)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertIn('sibF', v[17], str(v[17]))

    TEST_DATA_5 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familySibGender": 'male'}

    def test_family_sibling_gender_male(self):
        vs = do_query_variants(self.TEST_DATA_5)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        for v in vs:
            self.assertIn('sibM', v[17], str(v[17]))

    TEST_DATA_6 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyPrbGender": 'female'}

    def test_family_proband_gender_female(self):
        vs = do_query_variants(self.TEST_DATA_6)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        count = 0
        for v in vs:
            count += 1
            self.assertIn('prbF', v[17], str(v[17]))

        self.assertTrue(count > 0)

    TEST_DATA_7 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyPrbGender": 'male'}

    def test_family_proband_gender_male(self):
        vs = do_query_variants(self.TEST_DATA_7)
        cols = vs.next()
        logger.debug("cols: %s", str(cols))
        count = 0
        for v in vs:
            count += 1
            self.assertIn('prbM', v[17], str(v[17]))

        self.assertTrue(count > 0)


from api.dae_query import prepare_summary


class PreviewQueryTests(unittest.TestCase):
    PREVIEW_TEST_1 = {"genes": "All",
                      "geneTerm": "",
                      "geneSyms": "",
                      "geneRegion": "",
                      "denovoStudies": "allWE",
                      "transmittedStudies": "none",
                      "rarity": "ultraRare",
                      "inChild": "prbF",
                      "variantTypes": "All",
                      "effectTypes": "LGDs",
                      "families": "all",
                      "familyIds": "",
                      "familyRace": "All",
                      "familyVerbalIqLo": "",
                      "familyVerbalIqHi": "",
                      "familyQuadTrio": "All",
                      "familyPrbGender": "All",
                      "familySibGender": "All"}

    def test_preview_1(self):
        vs = do_query_variants(self.PREVIEW_TEST_1)
        cols = vs.next()
        count = 0
        for v in vs:
            count += 1
        self.assertTrue(count > 0)

    def test_preview_1_summary(self):
        vs = do_query_variants(self.PREVIEW_TEST_1)
        summary = prepare_summary(vs)
        self.assertTrue(int(summary["count"]) > 0)
