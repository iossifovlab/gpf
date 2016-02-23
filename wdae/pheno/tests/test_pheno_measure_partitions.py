'''
Created on Feb 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_gene_weights_partitions(self):
        url = "/api/v2/pheno_reports/measure_partitions"
        data = {
            "pheno_measure": "non_verbal_iq",
            "min": 9,
            "max": 50,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        print(response.data)
