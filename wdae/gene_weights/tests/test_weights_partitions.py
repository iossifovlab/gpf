'''
Created on Jan 28, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_gene_weights_partitions(self):
        url = "/api/v3/gene_weights/partitions"
        data = {
            "weight": "LGD_rank",
            "min": 1.5,
            "max": 5.0,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

    def test_gene_weights_partitions_rvis(self):
        url = "/api/v3/gene_weights/partitions"
        data = {
            "weight": "RVIS_rank",
            "min": 1,
            "max": 100,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

    def test_bad_gene_weight_partition(self):
        url = "/api/v3/gene_weights/partitions"
        data = {
            "weight": "ala-bala",
            "min": -8,
            "max": -3,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(404, response.status_code)

    def test_full_patition(self):
        url = "/api/v3/gene_weights/partitions"
        data = {
            "weight": "RVIS_rank",
            "min": 0,
            "max": 1000,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
