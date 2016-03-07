'''
Created on Feb 29, 2016

@author: lubo
'''
import unittest
from families.families_query import prepare_family_query


class Test(unittest.TestCase):

    def test_combined_family_pheno_measure(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
        }

        data = prepare_family_query(data)

        print(data)
        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)

        families = data['familyIds'].split(',')
        self.assertEqual(34, len(families))

    def test_combined_family_pheno_measure_and_quad(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
        }

        data = prepare_family_query(data)

        print(data)
        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)
        self.assertNotIn('familyQuadTrio', data)

        families = data['familyIds'].split(',')
        self.assertEqual(23, len(families))

    def test_combined_family_pheno_measure_and_quad_prb_gender_female(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
            'familyPrbGender': 'female',
        }

        data = prepare_family_query(data)

        print(data)
        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)
        self.assertNotIn('familyQuadTrio', data)
        self.assertNotIn('familyPrbGender', data)

        families = data['familyIds'].split(',')
        self.assertEqual(1, len(families))

    def test_combined_family_pheno_measure_and_quad_prb_gender_male(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
            'familyPrbGender': 'male',
        }

        data = prepare_family_query(data)

        print(data)
        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)
        self.assertNotIn('familyQuadTrio', data)
        self.assertNotIn('familyPrbGender', data)

        families = data['familyIds'].split(',')
        self.assertEqual(22, len(families))

    def test_combined_family_pheno_measure_and_and_race(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyRace': 'asian',
        }

        data = prepare_family_query(data)

        print(data)
        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)
        self.assertNotIn('familyRace', data)

        families = data['familyIds'].split(',')
        self.assertEqual(6, len(families))
