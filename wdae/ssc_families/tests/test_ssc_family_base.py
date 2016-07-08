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

    def test_prepare_base_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_family_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(4, len(family_ids))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_pheno_measure_with_family_ids(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
            'familyIds': '14525,13830',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2, len(family_ids))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_race(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'other',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(71, len(family_ids))

    def test_prepare_family_race_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'all',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_study_type_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'ALL',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_study_type_cnv(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'CNV',
        }

        family_ids = self.ssc_family_base.prepare_families(data)
        self.assertEquals(794, len(family_ids))
