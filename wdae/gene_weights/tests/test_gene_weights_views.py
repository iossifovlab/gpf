'''
Created on Dec 10, 2015

@author: lubo
'''
from __future__ import print_function
from rest_framework.test import APITestCase


class GeneWeightsListViewTest(APITestCase):

    def test_gene_weights_list_view(self):
        url = "/api/v3/gene_weights"
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(9, len(response.data))
        for w in response.data:
            self.assertIn('desc', w)
            self.assertIn('weight', w)
            self.assertIn('bars', w)
            self.assertIn('bins', w)


class GeneWeightsGetGenesViewTest(APITestCase):

    def test_gene_weights_get_genes_view(self):
        url = "/api/v3/gene_weights/genes"
        data = {
            "weight": "LGD_rank",
            "min": 1.5,
            "max": 5.0,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        print(response.data)

        self.assertEqual(3, len(response.data))
