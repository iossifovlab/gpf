import unittest
import itertools

#from DAE import vDB
from api.dae_query import dae_query_variants
from api.family_query import get_parents_race, get_verbal_iq


class FamilyRaceTests(unittest.TestCase):

    def test_asian_race(self):
        #studies = vDB.get_studies('allWEAndTG')
        query_string = {'denovoStudies': 'allWEAndTG',
                        'familyRace': 'asian'}
        vsl = dae_query_variants(query_string)
        par_race = get_parents_race()

        for v in itertools.chain(*vsl):
            self.assertEquals('asian', par_race[v.familyId])

    def test_african_amer_race(self):
        query_string = {'denovoStudies': 'allWEAndTG',
                        #'transmittedStudies': 'w873e374s322',
                        'familyRace': 'african-amer'}

        vsl = dae_query_variants(query_string)
        par_race = get_parents_race()

        for v in itertools.chain(*vsl):
            self.assertEquals('african-amer', par_race[v.familyId])


class FamilyVerbalIqTest(unittest.TestCase):

    def test_max_verbal_iq(self):
        #studies = vDB.get_studies('allWEAndTG')
        query_string = {'denovoStudies': 'allWEAndTG',
                        'familyVerbalIqHi': '50.0'}
        vsl = dae_query_variants(query_string)
        verb_iq = get_verbal_iq()

        for v in itertools.chain(*vsl):
            self.assertTrue(verb_iq[v.familyId] <= 50.0)

    def test_min_verbal_iq(self):
        #studies = vDB.get_studies('allWEAndTG')
        query_string = {'denovoStudies': 'allWEAndTG',
                        'familyVerbalIqLo': '50.0'}
        vsl = dae_query_variants(query_string)
        verb_iq = get_verbal_iq()

        for v in itertools.chain(*vsl):
            self.assertTrue(verb_iq[v.familyId] >= 50.0)


    def test_min_max_verbal_iq(self):
        #studies = vDB.get_studies('allWEAndTG')
        query_string = {'denovoStudies': 'allWEAndTG',
                        'familyVerbalIqLo': '50.0',
                        'familyVerbalIqHi': '90.0'}

        vsl = dae_query_variants(query_string)
        verb_iq = get_verbal_iq()

        for v in itertools.chain(*vsl):
            self.assertTrue(verb_iq[v.familyId] >= 50.0)
            self.assertTrue(verb_iq[v.familyId] <= 90.0)
