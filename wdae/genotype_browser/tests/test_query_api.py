'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
import copy


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


class Test(APITestCase):
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

        print(res['legend'])
        print(res['count'])
        self.assertEquals(3, len(res['legend']))
        self.assertEquals(422, int(res['count']))
        self.assertEquals(422, len(res['rows']))

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
