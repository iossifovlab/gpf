'''
Created on Jul 8, 2016

@author: lubo
'''
import unittest
from ssc_families.views import SSCFamilyBase


class SSCFiltersTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.ssc_family_base = SSCFamilyBase()

    def test_prepare_family_pheno_measure(self):
        data = {
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(4, len(family_ids['all']))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_pheno_measure_with_family_ids(self):
        data = {
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
            'familyIds': '14525,13830',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2, len(family_ids['all']))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_race(self):
        data = {
            'familyRace': 'other',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(71, len(family_ids['all']))

    def test_prepare_family_race_all(self):
        data = {
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 5,
            'familyPhenoMeasureMax': 200,
            'familyRace': 'all',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2757, len(family_ids['all']))

    def test_prepare_study_type_all(self):
        data = {
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 5,
            'familyPhenoMeasureMax': 200,
            'familyStudyType': 'ALL',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2757, len(family_ids['all']))

    def test_prepare_study_type_cnv(self):
        data = {
            'familyStudyType': 'CNV',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2856, len(family_ids['all']))

    def test_prepare_quad_and_study_type(self):
        data = {
            'familyStudyType': 'CNV',
            'familyQuadTrio': 'Quad',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2224, len(family_ids['all']))

    def test_prepare_probands_gender_male(self):
        data = {
            'familyPrbGender': 'male',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2471, len(family_ids['all']))

    def test_prepare_probands_gender_female(self):
        data = {
            'familyPrbGender': 'female',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(389, len(family_ids['all']))
