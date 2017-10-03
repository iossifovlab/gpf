import unittest
from helpers.wdae_query_variants import wdae_query_wrapper
import pytest

# LOGGER = logging.getLogger(__name__)


@pytest.mark.skip(reason="no way of currently testing this")
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
        vs = wdae_query_wrapper(self.TEST_DATA)
        vs.next()

        for v in vs:
            gl = v[9].split(';')
            self.assertEqual(1, gl.count('FMR1'))


@pytest.mark.skip(reason="no way of currently testing this")
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
                 'geneSet': 'Protein domains',
                 'variantTypes': 'All',
                 'familyQuadTrio': 'All',
                 'transmittedStudies': 'w1202s766e611',
                 'familyVerbalIqHi': '',
                 'familyRace': 'All',
                 'denovoStudies': 'allWEandTG'}

    def test_bad_region_exception(self):

        vs = wdae_query_wrapper(self.TEST_DATA)

        vs.next()
        for v in vs:
            self.assertIsNotNone(v)
