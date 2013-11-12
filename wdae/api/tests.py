"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from rest_framework.test import APIClient

from rest_framework import status
from rest_framework.test import APITestCase

import unittest

from api.dae_query import prepare_inchild, prepare_effect_types, \
                        prepare_variant_types, prepare_family_ids, prepare_gene_syms, \
                        prepare_gene_sets, prepare_denovo_studies, \
                        prepare_transmitted_studies, dae_query_variants, \
                        save_vs, generate_response


class FamiliesTest(APITestCase):
    client = APIClient()

    def test_families_get(self):
        response = self.client.get('/api/families/DalyWE2012')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')

    def test_families_get_filter(self):
        response = self.client.get('/api/families/DalyWE2012')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')
        self.assertEqual(len(data['families']), 174)

#     def test_families_post(self):
#         data={'studies':['DalyWE2012','EichlerTG2012']}
#         response=self.client.post('/api/families?filter="A"', data, format='json')
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)


# class GetVariantsTest(APITestCase):
#     client = APIClient()
#
#     def test_get_denovo_simple(self):
#         query={"denovoStudies":["DalyWE2012", "EichlerTG2012"]}
#         response=self.client.post("/api/get_variants_csv/",data=query,content_type='application/json')
#         self.assertEqual(response.status_code,status.HTTP_200_OK)
#


class InChildTests(unittest.TestCase):
    def test_inchild_empty(self):
        self.assertIsNone(prepare_inchild({}))
        self.assertIsNone(prepare_inchild({'inChild':None}))
        self.assertIsNone(prepare_inchild({'inChild':'None'}))
        self.assertIsNone(prepare_inchild({'inChild':'All'}))
        self.assertIsNone(prepare_inchild({'inChild':'none'}))


    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild({'inChild':'prb'}), 'prb')
        self.assertEqual(prepare_inchild({'inChild':'sib'}), 'sib')
        self.assertEqual(prepare_inchild({'inChild':'prbM'}), 'prbM')
        self.assertEqual(prepare_inchild({'inChild':'sibF'}), 'sibF')
        self.assertEqual(prepare_inchild({'inChild':'sibM'}), 'sibM')
        self.assertEqual(prepare_inchild({'inChild':'prbF'}), 'prbF')

    def test_inchild_not_correct(self):
        self.assertIsNone(prepare_inchild({'inChild':'prbMsibM'}))
        self.assertIsNone(prepare_inchild({'inChild':'prbMsibF'}))
        self.assertIsNone(prepare_inchild({'inChild':'ala-bala'}))


class EffectTypesTests(unittest.TestCase):
    ALL = """LGDs,CNVs,nonsynonymous,CNV-,CNV+,frame-shift,intron,no-frame-shift-new-stop,synonymous,nonsense,no-frame-shift,missense,3'UTR,5'UTR,splice-site"""
    def test_effect_types_all(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'All'}), self.ALL)

    def test_effect_types_none(self):
        self.assertIsNone(prepare_effect_types({}))
        self.assertIsNone(prepare_effect_types({'effectTypes':None}))
        self.assertIsNone(prepare_effect_types({'effectTypes':'None'}))
        self.assertIsNone(prepare_effect_types({'effectTypes':'none'}))

    def test_effect_types_correct(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'LGDs'}), 'LGDs')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNVs'}), 'CNVs')
        self.assertEqual(prepare_effect_types({'effectTypes':'nonsynonymous'}), 'nonsynonymous')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNV-'}), 'CNV-')
        self.assertEqual(prepare_effect_types({'effectTypes':'CNV+'}), 'CNV+')
        self.assertEqual(prepare_effect_types({'effectTypes':'frame-shift'}), 'frame-shift')
        self.assertEqual(prepare_effect_types({'effectTypes':'intron'}), 'intron')
        self.assertEqual(prepare_effect_types({'effectTypes':'no-frame-shift-new-stop'}), 'no-frame-shift-new-stop')
        self.assertEqual(prepare_effect_types({'effectTypes':'synonymous'}), 'synonymous')
        self.assertEqual(prepare_effect_types({'effectTypes':'nonsense'}), 'nonsense')
        self.assertEqual(prepare_effect_types({'effectTypes':'no-frame-shift'}), 'no-frame-shift')
        self.assertEqual(prepare_effect_types({'effectTypes':'missense'}), 'missense')
        self.assertEqual(prepare_effect_types({'effectTypes':"3'UTR"}), "3'UTR")
        self.assertEqual(prepare_effect_types({'effectTypes':"5'UTR"}), "5'UTR")
        self.assertEqual(prepare_effect_types({'effectTypes':"splice-site"}), "splice-site")

    def test_effect_types_not_correct(self):
        self.assertEqual(prepare_effect_types({'effectTypes':'ala-bala'}), self.ALL)


class VariantTypesTests(unittest.TestCase):

    def test_variant_types_all(self):
        self.assertIsNone(prepare_variant_types({'variantTypes':'All'}))

    def test_variant_type_none(self):
        self.assertIsNone(prepare_variant_types({}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'None'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'none'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : None}))

    def test_variant_types_correct(self):
        self.assertEqual(prepare_variant_types({'variantTypes':'CNV+'}), 'CNV+')
        self.assertEqual(prepare_variant_types({'variantTypes':'CNV-'}), 'CNV-')
        self.assertEqual(prepare_variant_types({'variantTypes':'snv'}), 'snv')
        self.assertEqual(prepare_variant_types({'variantTypes':'ins'}), 'ins')
        self.assertEqual(prepare_variant_types({'variantTypes':'del'}), 'del')

    def test_variant_type_not_correct(self):
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'ala'}))
        self.assertIsNone(prepare_variant_types({'variantTypes' : 'bala'}))



class FamilesTests(unittest.TestCase):

    def test_families_empty(self):
        self.assertIsNone(prepare_family_ids({}))

    def test_families_none(self):
        self.assertIsNone(prepare_family_ids({'familyIds' : 'None'}))
        self.assertIsNone(prepare_family_ids({'familyIds' : 'none'}))
        self.assertIsNone(prepare_family_ids({'familyIds' : 'All'}))
        self.assertIsNone(prepare_family_ids({'familyIds' : 'all'}))
        self.assertIsNone(prepare_family_ids({'familyIds' : None}))
        self.assertIsNone(prepare_family_ids({'familyIds' : 15}))

    def test_families_string(self):
        self.assertListEqual(prepare_family_ids({'familyIds' : '111'}), ['111'])
        self.assertListEqual(prepare_family_ids({'familyIds' : '111,222'}), ['111', '222'])
        self.assertListEqual(prepare_family_ids({'familyIds' : '111 , 222'}), ['111', '222'])
        self.assertListEqual(prepare_family_ids({'familyIds' : '111    ,    222'}), ['111', '222'])
        self.assertListEqual(prepare_family_ids({'familyIds' : '111     ,    222,'}), ['111', '222'])

    def test_families_list(self):
        self.assertListEqual(prepare_family_ids({'familyIds' : ['111']}), ['111'])
        self.assertListEqual(prepare_family_ids({'familyIds' : ['111', '222']}), ['111', '222'])


class GeneSymsTests(unittest.TestCase):

    def test_gen_syms_empty(self):
        self.assertIsNone(prepare_gene_syms({}))

    def test_gen_syms_none(self):
        self.assertIsNone(prepare_gene_syms({'geneSyms' : ''}))
        self.assertIsNone(prepare_gene_syms({'geneSyms' : '    '}))
        self.assertIsNone(prepare_gene_syms({'geneSyms' : None}))

    def test_gen_syms_correct_string(self):
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : 'CDH1'}), set(['CDH1']))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : 'CDH1,SCO2'}), set(['CDH1', 'SCO2']))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : 'CDH1      ,      SCO2'}), set(['CDH1', 'SCO2']))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : 'CDH1      ,      SCO2  ,   '}), set(['CDH1', 'SCO2']))

    def test_gen_syms_not_correct_string(self):
        self.assertIsNone(prepare_gene_syms({'geneSyms' : 'ala-bala'}))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : 'CDH1,ala-bala'}), set(['CDH1']))

    def test_gen_syms_correct_list(self):
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : ['CDH1']}), set(['CDH1']))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : ['CDH1', 'SCO2']}), set(['CDH1', 'SCO2']))

    def test_gen_syms_not_correct_list(self):
        self.assertIsNone(prepare_gene_syms({'geneSyms' : ['ala-bala']}))
        self.assertSetEqual(prepare_gene_syms({'geneSyms' : ['ala-bala', 'SCO2']}), set(['SCO2']))


class GeneSetsTests(unittest.TestCase):
    DISEASE_AIDS = set(['IFNG', 'KIR3DL1', 'CXCL12'])
    GO_GO_2001293 = set(['ACACA', 'ACACB'])
    MAIN_mPFC_maternal = set(['RAD23B', 'ADD2', 'NCOR2', 'CERS4', 'PPP1R3C', 'KCNK9', 'CLIP2', 'ARF3', 'ADAR', 'DEF8', 'SLC4A8', 'RFTN2', 'COPG2', 'LDHD', 'SPTLC2', 'KCTD20', 'NNT', 'IGF2', 'CLCN2', 'UBE2E2', 'HERC3', 'MEG3', 'TOB1', 'UBR4', 'ZNF157', 'AKAP2', 'DOPEY2', 'SCN1B', 'LIMCH1'])

    def test_gene_sets_empty(self):
        self.assertIsNone(prepare_gene_sets({}))

    def test_gete_sets_main(self):
        gs = prepare_gene_sets({'geneSet':{'gs_id':'main', 'gs_term':'mPFC_maternal'}})
        self.assertSetEqual(gs, self.MAIN_mPFC_maternal)
        self.assertTrue(isinstance(gs, set))

    def test_gete_sets_go(self):
        gs = prepare_gene_sets({'geneSet':{'gs_id':'GO', 'gs_term':'GO:2001293'}})
        self.assertSetEqual(gs, self.GO_GO_2001293)
        self.assertTrue(isinstance(gs, set))

    def test_gete_sets_disease(self):
        gs = prepare_gene_sets({'geneSet':{'gs_id':'disease', 'gs_term':'AIDS'}})
        self.assertSetEqual(gs, self.DISEASE_AIDS)
        self.assertTrue(isinstance(gs, set))


class StudiesTests(unittest.TestCase):

    def test_denovo_studies_empty(self):
        dsl = prepare_denovo_studies({'denovoStudies':[]})
        self.assertIsNone(dsl)

        dsl = prepare_denovo_studies({})
        self.assertIsNone(dsl)

    def test_denovo_studies_single(self):
        dsl = prepare_denovo_studies({'denovoStudies':["DalyWE2012"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "DalyWE2012")

        dsl = prepare_denovo_studies({'denovoStudies':["EichlerTG2012"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "EichlerTG2012")


    def test_denovo_studies_double(self):
        dsl = prepare_denovo_studies({'denovoStudies':["DalyWE2012", "EichlerTG2012"]})
        self.assertEquals(len(dsl), 2)

        self.assertEqual(dsl[0].name, "DalyWE2012")
        self.assertEqual(dsl[1].name, "EichlerTG2012")

    def test_denovo_studies_not_found(self):
        dsl = prepare_denovo_studies({'denovoStudies':["ala", "bala"]})
        self.assertIsNone(dsl)

    def test_transmitted_studies_empty(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':[]})
        self.assertIsNone(dsl)

        dsl = prepare_transmitted_studies({})
        self.assertIsNone(dsl)

    def test_transmitted_studies_single(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':["w873e374s322"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "w873e374s322")

        dsl = prepare_transmitted_studies({'transmittedStudies':["wig683"]})
        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "wig683")

    def test_transmitted_studies_double(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':["w873e374s322", "wig683"]})
        self.assertEquals(len(dsl), 2)

        self.assertEqual(dsl[0].name, "w873e374s322")
        self.assertEqual(dsl[1].name, "wig683")

    def test_transmitted_studies_not_found(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':["ala", "bala"]})
        self.assertIsNone(dsl)

import itertools

class VariantsTests(unittest.TestCase):

    def test_studies_empty(self):
        vs = dae_query_variants({'denovoStudies':[], 'transmittedStudies':[]})
        self.assertListEqual(vs, [])

        vs = dae_query_variants({})
        self.assertListEqual(vs, [])

    def test_studies_single(self):
        vs = dae_query_variants({'denovoStudies':["DalyWE2012"]})
        self.assertEqual(len(vs), 1)

        vs = dae_query_variants({'transmittedStudies':["wig683"]})
        self.assertEqual(len(vs), 1)

#     def test_effect_type(self):
#         vs = dae_query_variants({'denovoStudies':["DalyWE2012"],
#                                  'transmittedStudies':["wig683"],
#                                  'effectTypes':'nonsense'})
#         self.assertEqual(len(vs),2)
#         for v in itertools.chain(*vs):
#             self.assertEqual(v.atts['effectType'],'nonsense')


    def test_variant_filters(self):
        vs = dae_query_variants({"denovoStudies":["DalyWE2012"],
                                 "transmittedStudies":["wig683"],
                                 "inChild":"sibF",
                                 "effectTypes":"frame-shift",
                                 "variantTypes":"del",
                                 "ultraRareOnly":"True"})

        self.assertEqual(len(vs), 2)
        for v in itertools.chain(*vs):
            self.assertTrue('sibF' in v.inChS)
            self.assertEqual(v.atts['effectType'], 'frame-shift')

from GetVariantsInterface import augmentAVar

class CombinedTests(unittest.TestCase):


    TEST_DATA_1 = {"denovoStudies":["allWEAndTG"],
                 "transmittedStudies":["none"],
                 "inChild":"prbM",
                 "effectTypes":"All",
                 "variantTypes":"All",
                 "geneSet":{"gs_id":"main", "gs_term":"essentialGenes"},
                 "geneSyms":""}
    TEST_DATA_2 = {"denovoStudies":[],
                 "transmittedStudies":["w873e374s322"],
                 "inChild":"All",
                 "effectTypes":"All",
                 "variantTypes":"All",
                 "geneSet":{"gs_id":"GO", "gs_term":"GO:0022889"},
                 "geneSyms":"",
                 "ultraRareOnly":True}
    TEST_DATA_3 = {"denovoStudies":["allWEAndTG"],
                 "transmittedStudies":["wigEichler374"],
                 "inChild":"All",
                 "effectTypes":"All",
                 "variantTypes":"All",
                 "geneSet":{"gs_id":"GO", "gs_term":'GO:0022889'},
                 "geneSyms":"",
                 "ultraRareOnly":True}
    TEST_DATA_4 = {"denovoStudies":[],
                 "transmittedStudies":["wigEichler374"],
                 "inChild":"All",
                 "effectTypes":"All",
                 "variantTypes":"All",
                 "geneSet":None,
                 "geneRegion":"1:1018000-1020000",
                 "geneSyms":"",
                 "ultraRareOnly":True}


    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild(self.TEST_DATA_1), 'prbM')

    def test_gene_sets_main(self):
        gs = prepare_gene_sets(self.TEST_DATA_1)
        self.assertTrue(isinstance(gs, set))
        self.assertEqual(len(gs), 1747)


    def test_variants_gene_sets_1(self):
        vs = dae_query_variants(self.TEST_DATA_1)

        self.assertEqual(len(vs), 1)
        tf = open("test_data_1.tmp", "w+")

        save_vs(tf, itertools.imap(augmentAVar, itertools.chain(*vs)),
                ['effectType',
                 'effectDetails',
                 'all.altFreq',
                 'all.nAltAlls',
                 'all.nParCalled',
                 '_par_races_',
                 '_ch_prof_'])

#         for v in itertools.chain(*vs):
#             self.assertTrue('prbM' in v.inChS)

    def test_variants_gene_sets_3(self):
        vs = dae_query_variants(self.TEST_DATA_3)

        self.assertEqual(len(vs), 2)
        tf = open("test_data_3.tmp", "w+")


        for line in generate_response(itertools.imap(augmentAVar, itertools.chain(*vs)),
                                      ['effectType',
                                       'effectDetails',
                                       'all.altFreq',
                                       'all.nAltAlls',
                                       'all.nParCalled',
                                       '_par_races_',
                                       '_ch_prof_']):
            tf.write(line)
        tf.close()

    def test_variants_gene_sets_4(self):
        vs = dae_query_variants(self.TEST_DATA_4)

        self.assertEqual(len(vs), 1)
        tf = open("test_data_4.tmp", "w+")


        for line in generate_response(itertools.imap(augmentAVar, itertools.chain(*vs)),
                                      ['effectType',
                                       'effectDetails',
                                       'all.altFreq',
                                       'all.nAltAlls',
                                       'all.nParCalled',
                                       '_par_races_',
                                       '_ch_prof_']):
            tf.write(line)
        tf.close()

#         _safeVs(tf,itertools.imap(augmentAVar,itertools.chain(*vs)),
#                     ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'])


class QueryDictTests(unittest.TestCase):
    TEST_DATA_1 = "geneSymbols=&geneSet=main&geneSetInput=&denovoStudies=allWEAndTG&transmittedStudies=none&rarity=ultraRare&inChild=prb&variants=All&effectType=All&families="
