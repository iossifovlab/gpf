import unittest

from query_variants import do_query_variants

# from query_prepare import prepare_gene_sets
import logging
# import itertools

logger = logging.getLogger(__name__)


class PedigreeTests(unittest.TestCase):
    TEST_DATA_1 = {'geneRegionType': 'on', 'denovoStudies': 'wig1202', 'families': 'all', 'variantTypes': 'All', 'geneSyms': 'CERS2', 'familyVerbalIqLo': '', 'familyIds': '', 'inChild': 'All', 'rarity': 'ultraRare', 'geneTerm': '', 'effectTypes': 'LGDs', 'familySibGender': 'All', 'geneRegion': '', 'familyPrbGender': 'All', 'genes': 'Gene Symbols', 'familyQuadTrio': 'All', 'transmittedStudies': 'none', 'familyVerbalIqHi': '', 'familyRace': 'All', 'geneSet': 'main'}
    def test_pedigree_data_1(self):
        vs = do_query_variants(self.TEST_DATA_1, atts=["_pedigree_"])
        # vs.next()

        for v in vs:
            print v

    TEST_DATA_2 = {'geneRegionType': 'on', 'denovoStudies': 'LevyCNV2011', 'families': 'familyIds', 'variantTypes': 'All', 'geneSyms': '', 'familyVerbalIqLo': '', 'familyIds': '12096\r\n12418\r\n12239', 'inChild': 'All', 'rarity': 'ultraRare', 'geneTerm': '', 'effectTypes': 'All', 'familySibGender': 'All', 'geneRegion': '', 'familyPrbGender': 'All', 'genes': 'All', 'familyQuadTrio': 'All', 'transmittedStudies': 'none', 'familyVerbalIqHi': '', 'familyRace': 'All', 'geneSet': 'main'}
    def test_pedigree_data_2(self):
        vs = do_query_variants(self.TEST_DATA_2, atts=["_pedigree_"])
        # vs.next()

        for v in vs:
            print v

    # TEST_DATA_3 = {'geneRegionType': 'on', 'denovoStudies': 'LevyCNV2011', 'families': 'all', 'variantTypes': 'All', 'geneSyms': '', 'familyVerbalIqLo': '', 'familyIds': '', 'inChild': 'All', 'rarity': 'ultraRare', 'geneTerm': '', 'effectTypes': 'All', 'familySibGender': 'All', 'geneRegion': '', 'familyPrbGender': 'All', 'genes': 'All', 'familyQuadTrio': 'All', 'transmittedStudies': 'w1202s766e611', 'familyVerbalIqHi': '', 'familyRace': 'All', 'geneSet': 'main'}
    TEST_DATA_3 = {'geneRegionType': 'on', 'denovoStudies': 'LevyCNV2011', 'families': 'familyIds', 'variantTypes': 'All', 'geneSyms': '', 'familyVerbalIqLo': '', 'familyIds': '12561\r11689\r11092', 'inChild': 'All', 'rarity': 'ultraRare', 'geneTerm': '', 'effectTypes': 'All', 'familySibGender': 'All', 'geneRegion': '', 'familyPrbGender': 'All', 'genes': 'All', 'familyQuadTrio': 'All', 'transmittedStudies': 'none', 'familyVerbalIqHi': '', 'familyRace': 'All', 'geneSet': 'main'}
    def test_pedigree_data_3(self):
        vs = do_query_variants(self.TEST_DATA_3, atts=["_pedigree_"])
        # vs.next()

        for v in vs:
            print v
    