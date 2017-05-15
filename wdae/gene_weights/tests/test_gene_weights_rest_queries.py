'''
Created on Dec 11, 2015

@author: lubo
'''
import unittest
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

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
        self.assertEqual('19', response.data['count'])

    def test_rvis_rank_zero_to_one_in_autism(self):
        data = {
            "geneWeight": "RVIS_rank",
            "geneWeightMin": 0.0,
            "geneWeightMax": 1.0,
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('5', response.data['count'])

    def test_ssc_rest_call_by_gene_weight_rvis_25_to_30(self):
        data = {
            "geneWeight": "RVIS_rank",
            "geneWeightMin": 25,
            "geneWeightMax": 30,
            "gender": "female,male",
            'effectTypes':
            'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism only',
            'presentInParent': 'father only,mother and father,'
            'mother only,neither',
            'rarity': 'ultraRare',
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('9', response.data['count'])

    def test_ssc_rest_call_by_gene_syms(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'geneSyms': 'AHNAK2,MUC16',
            'gender': 'female,male',
            'rarity': 'ultraRare',
            'effectTypes':
            'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism only',
            'presentInParent': 'father only,mother and father,'
            'mother only,neither',
            'transmittedStudies': 'w1202s766e611',
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('15', response.data['count'])

    def test_sd_rest_call_by_gene_weight_rvis_25_to_30(self):

        data = {
            "geneWeight": "RVIS_rank",
            "geneWeightMin": 25,
            "geneWeightMax": 30,
            "gender": "female,male",
            'effectTypes': 'missense,synonymous',
            'phenoType': 'autism,unaffected',
        }

        url = '/api/sd_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('18', response.data['count'])

    def test_sd_rest_call_by_gene_syms(self):

        data = {
            'gender': 'female,male',
            'effectTypes': 'missense,synonymous',
            'phenoType': 'autism,unaffected',
            'variantTypes': 'del,ins,sub',
            'geneSyms': 'AHNAK2,MUC16'
        }

        url = '/api/sd_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])


if __name__ == "__main__":
    unittest.main()
