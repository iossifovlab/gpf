'''
Created on Jul 6, 2016

@author: lubo
'''
import unittest
from pheno_families.views import PhenoFamilyView


class PhenoMeasureFiltersTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.pheno_family_view = PhenoFamilyView()

    def test_prepare_base_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
        }

        family_ids = self.pheno_family_view.prepare(data)
        self.assertEquals(2756, len(family_ids))

    def test_prepare_family_pheno_measure(self):
        data = {
            'phenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 9,
            'familyPhenoMeasureMax': 15,
        }

        family_ids = self.pheno_family_view.prepare(data)
        self.assertEquals(4, len(family_ids))
        # ['14525', '13830', '13952', '13529']
