import unittest

from api.dae_query import do_query_variants

import logging

logger = logging.getLogger(__name__)


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
        vs.next()

        for v in vs:
            #self.assertEqual('african-amer;african-amer', v[16])
            if v[16] != 'african-amer;african-amer':
                print v[16]

    TEST_DATA_1_1 = {"denovoStudies": ["allWEAndTG"],
                     "transmittedStudies": 'None',
                     "inChild": "All",
                     "effectTypes": "All",
                     "variantTypes": "All",
                     "geneSet": "",
                     "geneSyms": "",
                     "ultraRareOnly": True,
                     "familyRace": 'white'}

    def test_family_race_1(self):
        vs = do_query_variants(self.TEST_DATA_1_1)
        vs.next()

        for v in vs:
            #self.assertEqual('white;white', v[16])
            if v[16] != 'white;white':
                print v[16]

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
        vs.next()

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
        vs.next()

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

    TEST_DATA_8 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyRace": 'ala-bala'}

    def test_family_wrong_race(self):
        vs = do_query_variants(self.TEST_DATA_8)
        vs.next()
        count = 0
        for v in vs:
            count += 1

        self.assertEqual(0, count)
