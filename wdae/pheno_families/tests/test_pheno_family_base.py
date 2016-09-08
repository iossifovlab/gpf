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

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2757, len(probands))

    def test_prepare_family_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(4, len(probands))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_pheno_measure_with_family_ids(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
            'familyIds': '14525,13830',
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2, len(probands))
        # ['14525', '13830', '13952', '13529']

    def test_prepare_family_race(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'other',
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(71, len(probands))

    def test_prepare_family_race_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyRace': 'all',
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2757, len(probands))

    def test_prepare_study_type_all(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'ALL',
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2757, len(probands))

    def test_prepare_study_type_cnv(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyStudyType': 'CNV',
        }

        probands = self.pheno_family_base.prepare_probands(data)
        self.assertEquals(2757, len(probands))


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
        self.assertEquals(2757, len(family_ids))
