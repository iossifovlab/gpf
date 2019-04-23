'''
Created on Dec 11, 2015

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from datasets_api.models import Dataset
import copy
from datasets.tests_old.requests import EXAMPLE_QUERY_SD, EXAMPLE_QUERY_SSC


class Test(BaseAuthenticatedUserTest):
    @classmethod
    def setUpTestData(cls):
        Dataset.recreate_dataset_perm('SD_TEST', [])
        Dataset.recreate_dataset_perm('SSC', [])
        Dataset.recreate_dataset_perm('SVIP', [])
        Dataset.recreate_dataset_perm('SPARKv1', [])
        Dataset.recreate_dataset_perm('SPARKv2', [])

    def test_rvis_rank_in_autism_zero_genes(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SD)
        data["geneWeights"] = {
            "weight": "RVIS_rank",
            "rangeStart": 1.0,
            "rangeEnd": 5.0
        }
        data["peopleGroup"] = {
            'id': "phenotype",
            "checkedValues": ["autism", ]
        }
        data['effectTypes'] = [
            'Frame-shift',
            'Nonsense',
            'Splice-site',
            'Missense',
            'Synonymous',
        ]

        url = '/api/v3/genotype_browser/preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('17', response.data['count'])

    def test_rvis_rank_zero_to_one_in_autism(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SD)
        data["geneWeights"] = {
            "weight": "RVIS_rank",
            "rangeStart": 16530,
            "rangeEnd": 16754
        }
        data["peopleGroup"] = {
            'id': "phenotype",
            "checkedValues": ["autism", ]
        }
        data['effectTypes'] = [
            'Frame-shift',
            'Nonsense',
            'Splice-site',
        ]

        url = '/api/v3/genotype_browser/preview'

#         data = {
#             "geneWeight": "RVIS_rank",
#             "geneWeightMin": 0.0,
#             "geneWeightMax": 1.0,
#             "denovoStudies": "TEST WHOLE EXOME",
#             "phenoType": "autism",
#             "gender": "female,male",
#         }
#
#         url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('9', response.data['count'])

    def test_ssc_rest_call_by_gene_weight_rvis_25_to_30(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SSC)
        data["geneWeights"] = {
            "weight": "RVIS_rank",
            "rangeStart": 25.0,
            "rangeEnd": 30.0
        }
        data["presentInChild"] = [
            "affected only",
        ]
        data["presentInParent"] = [
            'father only', 'mother only', 'mother and father', "neither"
        ]
        data['rarity'] = {
            'ultraRare': True,
        }

        url = '/api/v3/genotype_browser/preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('7', response.data['count'])

    def test_ssc_rest_call_by_gene_syms(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SSC)
        data["geneSymbols"] = 'AHNAK2,MUC16'
        data["presentInChild"] = [
            "affected only",
        ]
        data["presentInParent"] = [
            'father only', 'mother only', 'mother and father', "neither"
        ]
        data['rarity'] = {
            'ultraRare': True,
        }

        url = '/api/v3/genotype_browser/preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('15', response.data['count'])

    def test_sd_rest_call_by_gene_weight_rvis_25_to_30(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SD)
        data["geneWeights"] = {
            "weight": "RVIS_rank",
            "rangeStart": 25.0,
            "rangeEnd": 30.0
        }
        data["peopleGroup"] = {
            'id': "phenotype",
            "checkedValues": ["autism", "unaffected"]
        }
        data['effectTypes'] = [
            'Missense',
            'Synonymous',
        ]

        url = '/api/v3/genotype_browser/preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('17', response.data['count'])

    def test_sd_rest_call_by_gene_syms(self):
        data = copy.deepcopy(EXAMPLE_QUERY_SD)
        data["geneSymbols"] = 'AHNAK2,MUC16'
        data["peopleGroup"] = {
            'id': "phenotype",
            "checkedValues": ["autism", "unaffected"]
        }
        data['effectTypes'] = [
            'Missense',
            'Synonymous',
        ]

        url = '/api/v3/genotype_browser/preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])
