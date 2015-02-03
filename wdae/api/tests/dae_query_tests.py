import unittest

from query_variants import prepare_inchild, \
    dae_query_variants, \
    do_query_variants

from query_prepare import prepare_gene_sets
import logging
import itertools

logger = logging.getLogger(__name__)


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
    TEST_DATA_1 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": ["none"],
                   "inChild": "prbM",
                   "effectTypes": "frame-shift",
                   "variantTypes": "ins",
                   "geneSet": "main",
                   "geneTerm": "essentialGenes",
                   "geneSyms": ""}

    TEST_DATA_2 = {"denovoStudies": [],
                   "transmittedStudies": ["w873e374s322"],
                   "inChild": "prbF",
                   "effectTypes": "LoF",
                   "variantTypes": "All",
                   "geneSet": "GO",
                   "geneTerm": "GO:0022889",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_inchild_correct(self):
        self.assertEqual(prepare_inchild(self.TEST_DATA_1), set(['prbM']))

    def test_gene_sets_main(self):
        gs = prepare_gene_sets(self.TEST_DATA_1)
        self.assertTrue(isinstance(gs, set), "gene set: %s" % str(gs))
        # self.assertEqual(len(gs), 1747)

    def test_variants_gene_sets_1(self):
        vs = do_query_variants(self.TEST_DATA_1)
        vs.next()
        count = 0
        for v in vs:
            count += 1
            self.assertTrue('ins' in v[3], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbM' in v[6])
            self.assertTrue('frame-shift' in v[10])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('frame-shift' in v[13])
            self.assertTrue('prbM' in v[19])

        self.assertTrue(count > 0)

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
        vs.next()

        for v in vs:
            self.assertTrue('del' in v[3], "%s: %s" % (str(v[3]), str(v)))
            self.assertTrue('prbF' in v[6])
            self.assertTrue('frame-shift' in v[10])
            self.assertTrue('frame-shift' in v[11])
            self.assertTrue('frame-shift' in v[13])
            self.assertTrue('prbF' in v[19])


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
        vs.next()

        for v in vs:
            loc = int(v[2].split(':')[1])
            self.assertTrue(loc >= 1018000, "%s: %s" % (str(loc), str(v[2])))
            self.assertTrue(loc <= 1020000, "%s: %s" % (str(loc), str(v[2])))


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
                 'denovoStudies': 'cshlSSCWE'}

    def test_gene_region_filter(self):
        vs = do_query_variants(self.TEST_DATA)
        # vs.next()

        for v in vs:
            print v



class QueryDictTests(unittest.TestCase):
    TEST_DATA_1 = "geneSymbols=&geneSet=main&geneSetInput=&denovoStudies=allWEAndTG&transmittedStudies=none&rarity=ultraRare&inChild=prb&variants=All&effectType=All&families="



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
        vs.next()
        count = 0
        for v in vs:
            count += 1
        self.assertTrue(count > 0)

    def test_preview_1_summary(self):
        vs = do_query_variants(self.PREVIEW_TEST_1)
        summary = prepare_summary(vs)
        self.assertTrue(int(summary["count"]) > 0)
