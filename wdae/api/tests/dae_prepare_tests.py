import unittest

from api.dae_query import prepare_inchild, prepare_effect_types, \
    prepare_variant_types, prepare_family_ids, prepare_gene_syms, \
    prepare_gene_sets, prepare_denovo_studies, \
    prepare_transmitted_studies, dae_query_variants, \
    do_query_variants, load_gene_set

import logging
import itertools

logger = logging.getLogger(__name__)


class GeneSetsTests(unittest.TestCase):
    DENOVO_GENE_SET_1 = {'geneSet': 'denovo',
                         'geneStudy': 'StateWE2012',
                         'geneTerm': 'prbLGDs'}

    def test_denovo_gene_set(self):
        gs = prepare_gene_sets(self.DENOVO_GENE_SET_1)
        logger.debug("denovo gene sets: %s", str(gs))
        self.assertIsNotNone(gs)
        gt = load_gene_set('denovo', 'StateWE2012')
        self.assertSetEqual(set(gt.t2G['prbLGDs'].keys()), gs)

    DENOVO_GENE_SET_2 = {'geneSet': 'ala-bala',
                         'geneStudy': 'StateWE2012',
                         'geneTerm': 'portokala'}

    def test_none_gene_set(self):
        gs = prepare_gene_sets(self.DENOVO_GENE_SET_2)
        logger.debug("denovo gene sets: %s", str(gs))
        self.assertIsNone(gs)
        self.assertIsNone(prepare_gene_sets({'geneSet': 'denovo',
                                             'geneStudy': 'StateWE2012',
                                             'geneTerm': 'portokala'}))

        self.assertIsNone(prepare_gene_sets({'geneSet': 'main',
                                             'geneStudy': 'StateWE2012',
                                             'geneTerm': 'ala-bala'}))

    def test_main_does_not_depend_on_study_name(self):
        self.assertIsNotNone(prepare_gene_sets({'geneSet': 'main',
                                                'geneStudy': 'ala-bala',
                                                'geneTerm': 'E15-maternal'}))




class InChildTests(unittest.TestCase):
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


class EffectTypesTests(unittest.TestCase):
    ALL = """LGDs,CNVs,nonsynonymous,CNV-,CNV+,frame-shift,intron,no-frame-shift-new-stop,synonymous,nonsense,no-frame-shift,missense,3'UTR,5'UTR,splice-site"""

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
            prepare_effect_types({'effectTypes': 'LGDs'}), 'LGDs')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNVs'}), 'CNVs')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'nonsynonymous'}),
            'nonsynonymous')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNV-'}), 'CNV-')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'CNV+'}), 'CNV+')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'frame-shift'}), 'frame-shift')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'intron'}), 'intron')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'synonymous'}), 'synonymous')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'nonsense'}), 'nonsense')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'no-frame-shift'}),
            'no-frame-shift')
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'missense'}), 'missense')
        self.assertEqual(
            prepare_effect_types({'effectTypes': "3'UTR"}), "3'UTR")
        self.assertEqual(
            prepare_effect_types({'effectTypes': "5'UTR"}), "5'UTR")
        self.assertEqual(
            prepare_effect_types({'effectTypes': "splice-site"}),
            "splice-site")

    def test_effect_types_not_correct(self):
        self.assertEqual(
            prepare_effect_types({'effectTypes': 'ala-bala'}), None)


class VariantTypesTests(unittest.TestCase):

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
            prepare_variant_types({'variantTypes': 'CNV+'}), 'CNV+')
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'CNV-'}), 'CNV-')
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'snv'}), 'snv')
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'ins'}), 'ins')
        self.assertEqual(
            prepare_variant_types({'variantTypes': 'del'}), 'del')

    def test_variant_type_not_correct(self):
        self.assertIsNone(
            prepare_variant_types({'variantTypes': 'ala'}))
        self.assertIsNone(
            prepare_variant_types({'variantTypes': 'bala'}))
