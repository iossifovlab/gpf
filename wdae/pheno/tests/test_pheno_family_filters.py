'''
Created on Feb 29, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


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
        self.assertEqual(306, self.pos_count('LGDs', data))
        self.assertEqual(1783, self.neg_count('LGDs', data))

    def test_pheno_with_family_pheno_filter(self):
        url = "/api/v2/pheno_reports"
        data = {
            'phenoMeasure': 'head_circumference',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 60,

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual('head_circumference', response.data['measure'])
        self.assertEqual('head_circumference', response.data['formula'])

        data = response.data['data']
        self.assertEqual(58, self.pos_count('LGDs', data))
        self.assertEqual(2031, self.neg_count('LGDs', data))
