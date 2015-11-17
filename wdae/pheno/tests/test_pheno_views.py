'''
Created on Nov 16, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_default_view(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'phenoMeasure': 'head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        print(response.data)


class PhenoMeasuresTest(APITestCase):

    def test_get_pheno_measures(self):
        url = "/api/v2/pheno_reports/measures"
        response = self.client.get(url, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(75, len(response.data))

if __name__ == "__main__":
    unittest.main()
