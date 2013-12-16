import unittest

from api.family_query import advanced_family_filter, get_parents_race
from DAE import vDB
import logging


class FamilyRaceTests(unittest.TestCase):
    TEST_DATA_1 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyRace": 'african-amer'}

    TEST_DATA_2 = {"denovoStudies": ["allWEAndTG"],
                   "transmittedStudies": 'None',
                   "inChild": "All",
                   "effectTypes": "All",
                   "variantTypes": "All",
                   "geneSet": "",
                   "geneSyms": "",
                   "ultraRareOnly": True,
                   "familyRace": 'asian'}

    def test_family_race_african_amer(self):
        dsts = vDB.get_studies('allWEAndTG')
        races = get_parents_race()
        for dst in dsts:
            family_filters = advanced_family_filter(self.TEST_DATA_1, {})
            fs = family_filters(dst)
            for k in fs.keys():
                self.assertIn(k, races)
                self.assertEquals('african-amer', races[k])

    def test_family_race_asian(self):
        dsts = vDB.get_studies('allWEAndTG')
        races = get_parents_race()
        for dst in dsts:
            family_filters = advanced_family_filter(self.TEST_DATA_2, {})
            fs = family_filters(dst)
            for k in fs.keys():
                self.assertIn(k, races)
                self.assertEquals('asian', races[k])

