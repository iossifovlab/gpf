import unittest

from query_variants import prepare_inchild, \
    dae_query_variants, \
    do_query_variants

from query_prepare import prepare_gene_sets
import logging
import itertools

logger = logging.getLogger(__name__)

class IvanchoSubmittedDoubleGenesQueryTests(unittest.TestCase):
    TEST_DATA = {'geneRegionType': 'on',
                 'familyIds': '',
                 'genes': 'Gene Symbols',
                 'families': 'all',
                 'geneSyms': 'FMR1',
                 'familyVerbalIqLo': '',
                 'inChild': 'All',
                 'rarity': 'ultraRare',
                 'geneRegion': '',
                 'effectTypes': 'All',
                 'familySibGender': 'All',
                 'familyPrbGender': 'All',
                 'geneSet': 'main',
                 'variantTypes': 'All',
                 'familyQuadTrio': 'All',
                 'transmittedStudies': 'w1202s766e611',
                 'familyVerbalIqHi': '',
                 'familyRace': 'All',
                 'denovoStudies': 'allWEandTG'}

    def test_double_genes(self):
        vs = do_query_variants(self.TEST_DATA)
        vs.next()

        for v in vs:
            gl = v[8].split(';')
            print(v[8], gl, gl.count('FMR1'))
            self.assertEqual(1, gl.count('FMR1'))


class AlexPopovSubmittedBadRegionQueryTests(unittest.TestCase):
    TEST_DATA = {'geneRegionType': 'on',
                 'familyIds': '',
                 'genes': 'Gene Sets',
                 'families': 'all',
                 'geneSyms': '',
                 'familyVerbalIqLo': '',
                 'geneTerm': 'ANATO',
                 'geneStudy': 'allWEAndTG',
                 'inChild': 'All',
                 'rarity': 'ultraRare',
                 'geneRegion': '',
                 'effectTypes': 'LGDs',
                 'familySibGender': 'All',
                 'familyPrbGender': 'All',
                 'geneSet': 'domain',
                 'variantTypes': 'All',
                 'familyQuadTrio': 'All',
                 'transmittedStudies': 'w1202s766e611',
                 'familyVerbalIqHi': '',
                 'familyRace': 'All',
                 'denovoStudies': 'allWEandTG'}

    def test_bad_region_exception(self):
        
        vs = do_query_variants(self.TEST_DATA)
        
        vs.next()

        for v in vs:
            print v
            