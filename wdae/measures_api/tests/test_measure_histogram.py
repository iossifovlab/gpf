'''
Created on Mar 30, 2017

@author: lubo
'''


from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    URL = "/api/v3/measures/histogram"

    def test_non_verbal_iq_histogram(self):
        data = {
            "datasetId": "SSC",
            "measure": "pheno_common.non_verbal_iq",
        }
        response = self.client.post(self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('bins', data)
        self.assertIn('bars', data)
        self.assertIn('min', data)
        self.assertIn('max', data)

        self.assertEquals('pheno_common.non_verbal_iq', data['measure'])
        self.assertEquals(9.0, data['min'])
        self.assertEquals(161.0, data['max'])

        self.assertAlmostEqual(
            data['max'],
            max(data['bins']),
            delta=0.001
        )

        self.assertAlmostEqual(
            data['min'],
            min(data['bins']),
            delta=0.001
        )

    def test_bapq_average_histogram(self):
        data = {
            "datasetId": "SSC",
            "measure": "bapq.average",
        }
        response = self.client.post(self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('bins', data)
        self.assertIn('bars', data)
        self.assertIn('min', data)
        self.assertIn('max', data)

        self.assertEquals('bapq.average', data['measure'])

        self.assertAlmostEqual(
            data['max'],
            max(data['bins']),
            delta=0.001
        )

        self.assertAlmostEqual(
            data['min'],
            min(data['bins']),
            delta=0.001
        )
