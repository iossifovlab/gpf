'''
Created on Feb 29, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
import preloaded.register


class Test(APITestCase):

    @staticmethod
    def pos_count(effect, data):
        for vals in data:
            if vals[0] == effect:
                return vals[7]
        return None

    @staticmethod
    def neg_count(effect, data):
        for vals in data:
            if vals[0] == effect:
                return vals[8]
        return None

    def test_pheno_without_family_filters(self):
        url = "/api/v2/pheno_reports"
        data = {
            'phenoMeasure': 'head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual('head_circumference', response.data['measure'])
        self.assertEqual('head_circumference', response.data['formula'])

        data = response.data['data']
        self.assertEqual(312, self.pos_count('LGDs', data))
        self.assertEqual(2052, self.neg_count('LGDs', data))

    def test_family_pheno_filter_families_count(self):
        measures = preloaded.register.get_register().get('pheno_measures')
        families = measures.get_measure_families('non_verbal_iq', 0, 40)
        self.assertEquals(223, len(families))

    def test_pheno_with_family_pheno_filter(self):
        url = "/api/v2/pheno_reports"
        data = {
            'phenoMeasure': 'head_circumference',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 40,

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual('head_circumference', response.data['measure'])
        self.assertEqual('head_circumference', response.data['formula'])

        data = response.data['data']
        self.assertEqual(28, self.pos_count('LGDs', data))
        self.assertEqual(157, self.neg_count('LGDs', data))
