'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import status
import copy
from users_api.tests.base_tests import BaseAuthenticatedUserTest


EXAMPLE_REQUEST_SSC = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
    ],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "SSC",
    "pedigreeSelector": {
        "id": "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}

EXAMPLE_REQUEST_SD = {
    "datasetId": "SD_TEST",
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "variantTypes": [
        "del", "ins", "sub",
    ],
    "geneSet": {
        "geneSetsCollection": "main",
        "geneSet": "autism candidates from Iossifov PNAS 2015",
        "geneSetsTypes": []
    },
    "pedigreeSelector": {
        "id": "phenotype",
        "checkedValues": [
            "autism", "unaffected", "congenital_heart_disease",
            "epilepsy", "schizophrenia", "intellectual_disability"
        ]
    }
}


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/genotype_browser/preview"

    def test_query_preview(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertIn('cols', res)
        self.assertIn('rows', res)
        self.assertIn('count', res)
        self.assertIn('legend', res)

        self.assertEquals(3, len(res['legend']))
        # self.assertEquals(422, int(res['count']))
        self.assertEquals(427, int(res['count']))
        # self.assertEquals(422, len(res['rows']))
        self.assertEquals(427, len(res['rows']))

    def test_query_preview_with_gene_set(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SD)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(7, len(res['legend']))
        # self.assertEquals(264, int(res['count']))
        self.assertEquals(265, int(res['count']))
        # self.assertEquals(264, len(res['rows']))
        self.assertEquals(265, len(res['rows']))

    def test_missing_dataset(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        del data['datasetId']

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_bad_dataset(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        data['datasetId'] = 'ala bala portokala'

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
