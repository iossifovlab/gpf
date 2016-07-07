'''
Created on Jul 6, 2016

@author: lubo
'''
import unittest
from pheno_families.views import PhenoFamilyBase, PhenoFamilyCountersView


class PhenoMeasureFiltersTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.pheno_family_base = PhenoFamilyBase()

    def test_prepare_base_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_family_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
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

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2, len(family_ids))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_race(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'other',
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(71, len(family_ids))

    def test_prepare_family_race_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'all',
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_study_type_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'ALL',
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_study_type_cnv(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'CNV',
        }

        family_ids = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(771, len(family_ids))


class PhenoFamilyCountersViewTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.pheno_family_counters_view = PhenoFamilyCountersView()

    def test_prepare_check(self):

        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'CNV',
        }

        family_ids = self.pheno_family_counters_view.prepare_probands(data)
        self.assertEquals(771, len(family_ids))
