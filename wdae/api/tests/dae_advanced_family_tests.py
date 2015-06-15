import unittest

from query_variants import do_query_variants

import logging

LOGGER = logging.getLogger(__name__)


class AdvancedFamilyFilterTests(unittest.TestCase):
    TEST_DATA_1 = {"denovoStudies": ["ALL SSC"],
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
        count = 0
        fail = False
        for v in vs:
            count += 1
            #self.assertEqual('african-amer;african-amer', v[16])
            if v[21] != 'african-amer:african-amer':
                fail = True
        self.assertFalse(fail)
        self.assertTrue(count > 0)

    TEST_DATA_1_1 = {"denovoStudies": ["ALL SSC"],
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

        count = 0
        fail = False
        for v in vs:
            count += 1
            if v[21] != 'white:white':
                fail = True
        self.assertFalse(fail)
        self.assertTrue(count > 0)

    TEST_DATA_2 = {"denovoStudies": ["ALL SSC"],
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

        count = 0
        fail = False
        for v in vs:
            count += 1
            self.assertEqual(4, len(v[4].split('/')[0].split(' ')), str(v[4]))
        self.assertFalse(fail)
        self.assertTrue(count > 0)

    TEST_DATA_3 = {"denovoStudies": ["ALL SSC"],
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

        count = 0
        for v in vs:
            count += 1
            self.assertEqual(3, len(v[4].split('/')[0].split(' ')), str(v[4]))
        self.assertTrue(count > 0)

    TEST_DATA_4 = {"denovoStudies": ["ALL SSC"],
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
        vs.next()

        count = 0
        for v in vs:
            # self.assertIn('sibF', v[17], str(v[17]))
            count += 1
        self.assertTrue(count > 0)

    TEST_DATA_5 = {"denovoStudies": ["ALL SSC"],
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
        vs.next()

        count = 0
        for v in vs:
            # self.assertIn('sibM', v[17], str(v[17]))
            count += 1
        self.assertTrue(count > 0)

    TEST_DATA_6 = {"denovoStudies": ["ALL SSC"],
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
        LOGGER.info("cols: %s", str(cols))

        count = 0
        for v in vs:
            count += 1
            # self.assertIn('prbF', v[17], str(v[17]))

        self.assertTrue(count > 0)

    TEST_DATA_7 = {"denovoStudies": ["ALL SSC"],
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
        LOGGER.debug("cols: %s", str(cols))
        count = 0
        for v in vs:
            count += 1
            # self.assertIn('prbM', v[17], str(v[17]))

        self.assertTrue(count > 0)

    TEST_DATA_8 = {"denovoStudies": ["ALL SSC"],
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

    TEST_DATA_9_1 = {"denovoStudies": ["ALL SSC"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    TEST_DATA_9_2 = {"denovoStudies": ["ALL SSC"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def family_verbal_iq_test_count(self, data):
      vs = do_query_variants(data)
      vs.next()
      count = 0
      for v in vs:
        count += 1
      return count

    def test_family_verbal_iq(self):

      # Testing the base data with default filters
      count = self.family_verbal_iq_test_count(self.TEST_DATA_9_1)
      self.assertNotEqual(0, count)

      # Testing the familyVerbalIqLo filter compared to base data
      self.TEST_DATA_9_2['familyVerbalIqLo'] = 23;
      count_with_iq_lo = self.family_verbal_iq_test_count(self.TEST_DATA_9_2)
      self.assertNotEqual(0, count_with_iq_lo)
      self.assertTrue(count_with_iq_lo < count)

      # Testing the familyVerbalIqHi filter compared to base data
      self.TEST_DATA_9_2['familyVerbalIqLo'] = "";
      self.TEST_DATA_9_2['familyVerbalIqHi'] = 23;
      count_with_iq_hi = self.family_verbal_iq_test_count(self.TEST_DATA_9_2)
      self.assertNotEqual(0, count_with_iq_hi)
      self.assertTrue(count_with_iq_hi < count)

      # Testing the familyVerbalIqLo filter with wrong data compared to 0.0
      self.TEST_DATA_9_2['familyVerbalIqHi'] = "";
      self.TEST_DATA_9_2['familyVerbalIqLo'] = 'foo'
      count_with_iq_lo_wrong = self.family_verbal_iq_test_count(self.TEST_DATA_9_2)
      self.assertNotEqual(0, count_with_iq_lo_wrong)
      # self.TEST_DATA_9_2['familyVerbalIqLo'] = '0.0'
      # count_with_iq_lo_ok = self.family_verbal_iq_test_count(self.TEST_DATA_9_2)
      # self.assertEqual(count_with_iq_lo_wrong, count_with_iq_lo_ok)

      # Testing the familyVerbalIqHi filter with wrong data
      self.TEST_DATA_9_2['familyVerbalIqHi'] = 'foo';
      self.TEST_DATA_9_2['familyVerbalIqLo'] = ''
      count_with_iq_hi_wrong = self.family_verbal_iq_test_count(self.TEST_DATA_9_2)
      self.assertNotEqual(0, count_with_iq_hi_wrong)

    TEST_DATA_10 = {"denovoStudies": ["ALL SSC"],
                   "transmittedStudies": 'None',
                   "inChild": "prb",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_in_child(self):
        vs = do_query_variants(self.TEST_DATA_10)
        cols = vs.next()
        count = 0
        for v in vs:
            count += 1
            self.assertIn('prb', v[6], str(v[6]))

        self.assertTrue(count > 0)

    TEST_DATA_11 = {"denovoStudies": ["ALL SSC"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "del",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True}

    def test_variant_types(self):
      vs = do_query_variants(self.TEST_DATA_11)
      cols = vs.next()
      count = 0
      for v in vs:
          count += 1
          self.assertIn('del', v[3], str(v[3]))

      self.assertTrue(count > 0)



