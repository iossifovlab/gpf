'''
Created on Dec 11, 2015

@author: lubo
'''
import unittest
from rest_framework import status
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_rvis_rank_in_autism_zero_genes(self):
        data = {
            "geneWeight": "RVIS_rank",
            "geneWeightMin": 1.0,
            "geneWeightMax": 5.0,
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('18', response.data['count'])

    def test_rvis_rank_zero_to_one_in_autism(self):
        data = {
            "geneWeight": "RVIS",
            "geneWeightMin": 0.0,
            "geneWeightMax": 0.0,
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('26', response.data['count'])

if __name__ == "__main__":
    unittest.main()
