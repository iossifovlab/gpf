import unittest

from query_variants import prepare_inchild, \
    dae_query_variants

from helpers.dae_query import prepare_summary


import logging
import itertools
from helpers.wdae_query_variants import prepare_gene_sets, wdae_query_wrapper
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="no way of currently testing this")
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

        vs = dae_query_variants({'transmittedStudies': ["w1202s766e611"]})
        self.assertEqual(len(vs), 1)

    def test_variant_filters(self):
        vs = dae_query_variants({"denovoStudies": ["DalyWE2012"],
                                 "transmittedStudies": ["w1202s766e611"],
                                 "inChild": "sibF",
                                 "effectTypes": "frame-shift",
                                 "variantTypes": "del",
                                 "ultraRareOnly": "True"})

        self.assertEqual(len(vs), 2)
        fail = False
        for v in itertools.chain(*vs):
            self.assertTrue('sibF' in v.inChS)
            if 'frame-shift' not in v.atts['effectGene']:
                fail = True

        # self.assertEqual(v.atts['effectType'], 'frame-shift')
        self.assertFalse(fail)


@pytest.mark.skip(reason="no way of currently testing this")
class CombinedTests(unittest.TestCase):
    TEST_DATA_1 = {"denovoStudies": ["ALL WHOLE EXOME"],
                   "transmittedStudies": ["none"],
                   "inChild": "prbM",
                   "effectTypes": "frame-shift",
                   "variantTypes": "ins",
                   "geneSet": "main",
                   "geneTerm": "essential genes",
                   "geneSyms": ""}

    TEST_DATA_2 = {"denovoStudies": [],
                   "transmittedStudies": ["w1202s766e611"],
                   "inChild": "prbF",
                   "effectTypes": "LoF",
                   "variantTypes": "All",
                   "geneSet": "GO",
                   "geneTerm": "GO:0022889",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild(self.TEST_DATA_1), 'prbM')

    def test_gene_sets_main(self):
        gs = prepare_gene_sets(self.TEST_DATA_1)
        self.assertTrue(isinstance(gs, set), "gene set: %s" % str(gs))
        # self.assertEqual(len(gs), 1747)

    def test_variants_gene_sets_1(self):
        vs = wdae_query_wrapper(self.TEST_DATA_1)
        next(vs)
        count = 0
        for v in vs:
            count += 1
            self.assertTrue('ins' in v[4], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbM' in v[7])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('frame-shift' in v[12])
            self.assertTrue('frame-shift' in v[14])
            self.assertTrue('prbM' in v[23])

        self.assertTrue(count > 0)

    TEST_DATA_3 = {"denovoStudies": ["ALL WHOLE EXOME"],
                   "transmittedStudies": [],
                   "inChild": "prbF",
                   "effectTypes": "frame-shift",
                   "variantTypes": "del",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_variants_gene_sets_3(self):
        vs = wdae_query_wrapper(self.TEST_DATA_3)
        next(vs)

        for v in vs:
            self.assertTrue('del' in v[4], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbF' in v[7])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('frame-shift' in v[12])
            self.assertTrue('frame-shift' in v[14])
            self.assertTrue('prbF' in v[23])


@pytest.mark.skip(reason="no way of currently testing this")
class GeneRegionCombinedTests(unittest.TestCase):
    TEST_DATA = {"denovoStudies": [],
                 "transmittedStudies": ["w1202s766e611"],
                 "inChild": "All",
                 "effectTypes": "All",
                 "variantTypes": "All",
                 "geneSet": None,
                 "geneRegion": "1:1018000-1020000",
                 "geneSyms": "",
                 "ultraRareOnly": True}

    def test_gene_region_filter(self):
        vs = wdae_query_wrapper(self.TEST_DATA)
        next(vs)

        for v in vs:
            loc = int(v[3].split(':')[1])
            self.assertTrue(loc >= 1018000, "%s: %s" % (str(loc), str(v[3])))
            self.assertTrue(loc <= 1020000, "%s: %s" % (str(loc), str(v[3])))


@pytest.mark.skip(reason="no way of currently testing this")
class IvanchoSubmittedQueryTests(unittest.TestCase):
    TEST_DATA = {'geneRegionType': 'on',
                 'familyIds': '',
                 'genes': 'Gene Symbols',
                 'families': 'all',
                 'geneSyms': 'AARS\r\n,ABCD1',
                 'familyVerbalIqLo': '',
                 'geneTerm': '',
                 'geneStudy': 'allWEAndTG',
                 'inChild': 'All',
                 'rarity': 'ultraRare',
                 'geneRegion': '',
                 'effectTypes': 'LGDs',
                 'familySibGender': 'All',
                 'familyPrbGender': 'All',
                 'geneSet': 'main',
                 'variantTypes': 'All',
                 'familyQuadTrio': 'All',
                 'transmittedStudies': 'w1202s766e611',
                 'familyVerbalIqHi': '',
                 'familyRace': 'All',
                 'denovoStudies': "ALL WHOLE EXOME"}

    def test_gene_region_filter(self):
        vs = wdae_query_wrapper(self.TEST_DATA)
        # vs.next()
        count = 0
        for _v in vs:
            count += 1
        self.assertTrue(count > 0)


@pytest.mark.skip(reason="no way of currently testing this")
class PreviewQueryTests(unittest.TestCase):
    PREVIEW_TEST_1 = {"genes": "All",
                      "geneTerm": "",
                      "geneSyms": "",
                      "geneRegion": "",
                      "denovoStudies": "ALL WHOLE EXOME",
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
        vs = wdae_query_wrapper(self.PREVIEW_TEST_1)
        next(vs)
        count = 0
        for _v in vs:
            count += 1
        self.assertTrue(count > 0)

    def test_preview_1_summary(self):
        vs = wdae_query_wrapper(self.PREVIEW_TEST_1)
        summary = prepare_summary(vs)
        self.assertTrue(int(summary["count"]) > 0)
