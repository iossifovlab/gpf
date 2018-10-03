'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import status
import copy
from users_api.tests.base_tests import BaseAuthenticatedUserTest


EXAMPLE_REQUEST_SVIP = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "SVIP",
    "pedigreeSelector": {
        "id": "16pstatus",
        "checkedValues": [
            "deletion",
            "duplication",
            "triplication",
            "negative"]
    }
}


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/genotype_browser/preview"

    def test_query_preview(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SVIP)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertIn('cols', res)
        self.assertIn('rows', res)
        self.assertIn('count', res)
        self.assertIn('legend', res)

        self.assertEquals(63, int(res['count']))
        self.assertEquals(63, len(res['rows']))

        self.assertEquals(5, len(res['legend']))
        self.assertEquals('deletion', res['legend'][0]['id'])

    def test_query_preview_other_pedigree_selector(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SVIP)
        data['pedigreeSelector'] = {
            "id": "phenotype",
            "checkedValues": [
                "ASD and other neurodevelopmental disorders",
                "unaffected"
            ]
        }

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertIn('cols', res)
        self.assertIn('rows', res)
        self.assertIn('count', res)
        self.assertIn('legend', res)

        self.assertEquals(63, int(res['count']))
        self.assertEquals(63, len(res['rows']))

        self.assertEquals(3, len(res['legend']))
        self.assertEquals(
            'ASD and other neurodevelopmental disorders',
            res['legend'][0]['id'])
