
from builtins import str
from query_prepare import prepare_gene_syms, \
    prepare_denovo_studies, \
    prepare_transmitted_studies
from query_variants import prepare_inchild, prepare_effect_types, \
    prepare_variant_types, prepare_family_ids


import logging
from rest_framework.test import APITestCase
from helpers.wdae_query_variants import prepare_gene_sets, gene_set_loader2
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="no way of currently testing this")
class InChildTests(APITestCase):

    def test_inchild_empty(self):
        self.assertIsNone(prepare_inchild({}))
        self.assertIsNone(prepare_inchild({'inChild': None}))
        self.assertIsNone(prepare_inchild({'inChild': 'None'}))
        self.assertIsNone(prepare_inchild({'inChild': 'All'}))
        self.assertIsNone(prepare_inchild({'inChild': 'none'}))

    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild({'inChild': 'prb'}), 'prb')
        self.assertEqual(prepare_inchild({'inChild': 'sib'}), 'sib')
        self.assertEqual(prepare_inchild({'inChild': 'prbM'}), 'prbM')
        self.assertEqual(prepare_inchild({'inChild': 'sibF'}), 'sibF')
        self.assertEqual(prepare_inchild({'inChild': 'sibM'}), 'sibM')
        self.assertEqual(prepare_inchild({'inChild': 'prbF'}), 'prbF')

    def test_inchild_not_correct(self):
        self.assertIsNone(prepare_inchild({'inChild': 'prbMsibM'}))
        self.assertIsNone(prepare_inchild({'inChild': 'prbMsibF'}))
        self.assertIsNone(prepare_inchild({'inChild': 'ala-bala'}))


@pytest.mark.skip(reason="no way of currently testing this")
class EffectTypesTests(APITestCase):
    ALL = """LGDs,CNVs,nonsynonymous,CNV-,CNV+,frame-shift,intron,""" \
        """no-frame-shift-new-stop,synonymous,nonsense,no-frame-shift,""" \
        """missense,3'UTR,5'UTR,splice-site"""

    def test_effect_types_all(self):
        self.assertEqual(prepare_effect_types({'effectTypes': 'All'}),
                         None)

    def test_effect_types_none(self):
        self.assertIsNone(prepare_effect_types({}))
        self.assertIsNone(prepare_effect_types({'effectTypes': None}))
        self.assertIsNone(prepare_effect_types({'effectTypes': 'None'}))
        self.assertIsNone(prepare_effect_types({'effectTypes': 'none'}))

    def test_effect_types_correct(self):
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'LGDs'}),
            ['no-frame-shift-newStop', 'frame-shift',
             'nonsense', 'splice-site'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNVs'}),
            ['CNV-', 'CNV+'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'nonsynonymous'}),
            ['noStart', 'frame-shift', 'noEnd', 'nonsense',
             'no-frame-shift-newStop', 'no-frame-shift', 'missense',
             'CDS', 'splice-site'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNV-'}), ['CNV-'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNV+'}), ['CNV+'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'frame-shift'}),
            ['frame-shift'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'intron'}),
            ['intron'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'synonymous'}),
            ['synonymous'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'nonsense'}),
            ['nonsense'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'no-frame-shift'}),
            ['no-frame-shift'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'missense'}),
            ['missense'])
        self.assertEqual(
            prepare_effect_types({'effectTypes': "3'UTR"}),
            ["3'UTR"])
        self.assertEqual(
            prepare_effect_types({'effectTypes': "5'UTR"}),
            ["5'UTR"])
        self.assertEqual(
            prepare_effect_types({'effectTypes': "splice-site"}),
            ["splice-site"])

    def test_effect_types_not_correct(self):
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'ala-bala'}), None)


@pytest.mark.skip(reason="no way of currently testing this")
class VariantTypesTests(APITestCase):

    def test_variant_types_all(self):
        self.assertIsNone(
            prepare_variant_types({'variantTypes': 'All'}))

    def test_variant_type_none(self):
        self.assertIsNone(prepare_variant_types({}))
        self.assertIsNone(prepare_variant_types({'variantTypes': 'None'}))
        self.assertIsNone(prepare_variant_types({'variantTypes': 'none'}))
        self.assertIsNone(prepare_variant_types({'variantTypes': None}))

    def test_variant_types_correct(self):
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'CNV'}), ['CNV'])
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'sub'}), ['sub'])
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'ins'}), ['ins'])
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'del'}), ['del'])

    def test_variant_type_not_correct(self):
        self.assertIsNone(
            prepare_variant_types({'variantTypes': 'ala'}))
        self.assertIsNone(
            prepare_variant_types({'variantTypes': 'bala'}))


@pytest.mark.skip(reason="no way of currently testing this")
class FamilesTests(APITestCase):

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


@pytest.mark.skip(reason="no way of currently testing this")
class GeneSymsTests(APITestCase):

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


@pytest.mark.skip(reason="no way of currently testing this")
class GeneSetsTests(APITestCase):

    DISEASE_AIDS = set(['IFNG', 'KIR3DL1', 'CXCL12'])
    GO_GO_2001293 = set(['ACACA', 'ACACB'])

    def test_gene_sets_empty(self):
        self.assertIsNone(prepare_gene_sets({}))

    def test_gete_sets_go(self):
        gs = prepare_gene_sets({'geneSet': 'GO', 'geneTerm': 'GO:2001293'})
        self.assertSetEqual(gs, self.GO_GO_2001293)
        self.assertTrue(isinstance(gs, set))

    def test_gete_sets_disease(self):
        gs = prepare_gene_sets({'geneSet': 'disease', 'geneTerm': 'AIDS'})
        self.assertSetEqual(gs, self.DISEASE_AIDS)
        self.assertTrue(isinstance(gs, set))

    DENOVO_GENE_SET_1 = {'geneSet': 'denovo',
                         'gene_set_phenotype': 'autism',
                         'geneTerm': 'Missense'}

    def test_denovo_gene_set(self):
        gs = prepare_gene_sets(self.DENOVO_GENE_SET_1)
        LOGGER.debug("denovo gene sets: %s", str(gs))
        self.assertIsNotNone(gs)
        gt = gene_set_loader2('denovo', 'autism')
        self.assertSetEqual(set(gt.t2G['Missense'].keys()), gs)

    DENOVO_GENE_SET_2 = {'geneSet': 'ala-bala',
                         'gene_set_phenotype': 'ala-bala',
                         'geneTerm': 'portokala'}

    def test_none_gene_set(self):
        gs = prepare_gene_sets(self.DENOVO_GENE_SET_2)
        LOGGER.info("denovo gene sets: %s", str(gs))
        self.assertIsNone(gs)
        self.assertIsNone(prepare_gene_sets({'geneSet': 'denovo',
                                             'gene_set_phenotype': 'autism',
                                             'geneTerm': 'portokala'}))

        self.assertIsNone(prepare_gene_sets({'geneSet': 'main',
                                             'gene_set_phenotype': 'autism',
                                             'geneTerm': 'ala-bala'}))

    def test_main_does_not_depend_on_study_name(self):
        self.assertIsNotNone(prepare_gene_sets(
            {'geneSet': 'main',
             'gene_set_phenotype': 'ala-bala',
             'geneTerm': 'PSD'}))


@pytest.mark.skip(reason="no way of currently testing this")
class StudiesTests(APITestCase):

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
                                           ["w1202s766e611"]})

        self.assertEquals(len(dsl), 1)
        self.assertEqual(dsl[0].name, "w1202s766e611")

#         dsl = prepare_transmitted_studies({'transmittedStudies':
#                                            ["wig683"]})
#         self.assertEquals(len(dsl), 1)
#         self.assertEqual(dsl[0].name, "wig683")

#     def test_transmitted_studies_double(self):
#         dsl = prepare_transmitted_studies({'transmittedStudies':
#                                            ["w873e374s322", "wig683"]})
#         self.assertEquals(len(dsl), 2)
#
#         self.assertEqual(dsl[0].name, "w873e374s322")
#         self.assertEqual(dsl[1].name, "wig683")

    def test_transmitted_studies_not_found(self):
        dsl = prepare_transmitted_studies({'transmittedStudies':
                                           ["ala", "bala"]})
        self.assertIsNone(dsl)
