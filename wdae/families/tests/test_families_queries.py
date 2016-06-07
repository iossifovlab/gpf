'''
Created on Feb 29, 2016

@author: lubo
'''
import unittest
from families.families_query import prepare_family_query, parse_family_ids
from DAE import vDB


class Test(unittest.TestCase):

    def test_combined_family_pheno_measure(self):
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
        }

        fst, data = prepare_family_query(data)
        self.assertEquals("ALL", fst)

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

        fst, data = prepare_family_query(data)
        self.assertEquals("ALL", fst)

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

        fst, data = prepare_family_query(data)
        self.assertEquals("ALL", fst)

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

        fst, data = prepare_family_query(data)
        self.assertEquals("ALL", fst)

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

        fst, data = prepare_family_query(data)
        self.assertEquals("ALL", fst)

        self.assertIn('familyIds', data)
        self.assertNotIn('familyPhenoMeasure', data)
        self.assertNotIn('familyPhenoMeasureMin', data)
        self.assertNotIn('familyPhenoMeasureMax', data)
        self.assertNotIn('familyRace', data)

        families = data['familyIds'].split(',')
        self.assertEqual(6, len(families))

    def test_combined_family_study_type_and_study(self):
        data = {
            'familyStudyType': 'WE',
            'familyStudies': 'IossifovWE2014',
        }

        fst, data = prepare_family_query(data)
        self.assertEquals("WE", fst)

        self.assertIn('familyIds', data)
        family_ids1 = parse_family_ids(data)

        study = vDB.get_study('IossifovWE2014')
        family_ids2 = set(study.families.keys())
        self.assertEquals(0, len(family_ids1.difference(family_ids2)))

    def test_combined_family_study_type_and_study_cnv(self):
        data = {
            'familyStudyType': 'CNV',
            'familyStudies': 'IossifovWE2014',
        }

        fst, data = prepare_family_query(data)
        self.assertEquals("CNV", fst)

        self.assertIn('familyIds', data)
        family_ids = parse_family_ids(data)

        self.assertIsNone(family_ids)
