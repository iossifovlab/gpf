import unittest

from query_variants import prepare_inchild, \
    dae_query_variants, \
    do_query_variants

from query_prepare import prepare_gene_sets
import logging
import itertools

logger = logging.getLogger(__name__)

class IvanchoSubmittedQueryTests(unittest.TestCase):
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
        # vs.next()

        for v in vs:
            print(v[8])
            gl = v[8].split(';')
            print(gl)
            print(gl.count('FMR1'))
            self.assertEqual(1, gl.count('FMR1'))

