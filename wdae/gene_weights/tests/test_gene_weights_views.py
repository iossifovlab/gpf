'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase


class GeneWeightsListViewTest(APITestCase):

    def test_gene_weights_list_view(self):
        url = "/api/v2/gene_weights"
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        print(response.data)
        self.assertEqual(4, len(response.data))
        for w in response.data:
            self.assertIn('min', w)
            self.assertIn('max', w)
            self.assertIn('desc', w)
            self.assertIn('weight', w)
            self.assertIn('bars', w)
            self.assertIn('bins', w)


class GeneWeightsGetGenesViewTest(APITestCase):

    def test_gene_weights_get_genes_view(self):
        url = "/api/v2/gene_weights/genes"
        data = {
            "weight": "LGD_rank",
            "min": 1.5,
            "max": 5.0,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        print(response.data)
        self.assertEqual(4, len(response.data))

if __name__ == "__main__":
    unittest.main()
