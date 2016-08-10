'''
Created on Feb 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_gene_weights_partitions(self):
        url = "/api/v2/pheno_reports/measure_histogram"
        data = {
            "measure": "non_verbal_iq",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('bars', response.data)
        self.assertIn('bins', response.data)
        self.assertIn('measure', response.data)
        self.assertIn('min', response.data)
        self.assertIn('max', response.data)
        self.assertIn('step', response.data)
