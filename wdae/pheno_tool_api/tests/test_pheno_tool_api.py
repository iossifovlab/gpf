'''
Created on Jul 7, 2017

@author: lubo
'''
from __future__ import print_function
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from rest_framework import status
from pprint import pprint


class Test(BaseAuthenticatedUserTest):

    TOOL_URL = "/api/v3/pheno_tool"

    def test_simple_query_lgds(self):
        query = {
            "datasetId": "SSC",
            "measureId": "ssc_hwhc.head_circumference",
            "normalizeBy": [
                "age",
                "non-verbal iq"
            ],
            "geneSet": {
                "geneSetsCollection": "main",
                "geneSet": "autism candidates from Sanders Neuron 2015",
                "geneSetsTypes": []
            },
            "presentInParent": {
                "presentInParent": [
                    "neither"
                ],
            },
            "effectTypes": [
                "LGDs",
            ]
        }
        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        pprint(response.data)
        result = response.data['results'][0]
        self.assertEqual(result['effect'], 'LGDs')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            352
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            19
        )
        self.assertEqual(
            result['maleResults']['negative']['count'],
            2290
        )
        self.assertEqual(
            result['maleResults']['positive']['count'],
            67
        )

    def test_simple_query_missense(self):
        query = {
            "datasetId": "SSC",
            "measureId": "ssc_hwhc.head_circumference",
            "normalizeBy": [
                "age",
                "non-verbal iq"
            ],
            "geneSet": {
                "geneSetsCollection": "main",
                "geneSet": "autism candidates from Sanders Neuron 2015",
                "geneSetsTypes": []
            },
            "presentInParent": {
                "presentInParent": [
                    "neither"
                ],
            },
            "effectTypes": [
                "Missense",
            ]
        }
        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]
        self.assertEqual(result['effect'], 'Missense')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            363
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            8
        )
        self.assertEqual(
            result['maleResults']['negative']['count'],
            2314
        )
        self.assertEqual(
            result['maleResults']['positive']['count'],
            43
        )

    def test_simple_query_synonymous(self):
        query = {
            "datasetId": "SSC",
            "measureId": "ssc_hwhc.head_circumference",
            "normalizeBy": [
                "age",
                "non-verbal iq"
            ],
            "geneSet": {
                "geneSetsCollection": "main",
                "geneSet": "autism candidates from Sanders Neuron 2015",
                "geneSetsTypes": []
            },
            "presentInParent": {
                "presentInParent": [
                    "neither"
                ],
            },
            "effectTypes": [
                "Synonymous",
                #                 "CNV"
            ]
        }
        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]
        self.assertEqual(result['effect'], 'Synonymous')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            371
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            0
        )
        self.assertEqual(
            result['maleResults']['negative']['count'],
            2353
        )
        self.assertEqual(
            result['maleResults']['positive']['count'],
            4
        )

    def test_simple_query_cnvs(self):
        query = {
            "datasetId": "SSC",
            "measureId": "ssc_hwhc.head_circumference",
            "normalizeBy": [
                "age",
                "non-verbal iq"
            ],
            "geneSet": {
                "geneSetsCollection": "main",
                "geneSet": "autism candidates from Sanders Neuron 2015",
                "geneSetsTypes": []
            },
            "presentInParent": {
                "presentInParent": [
                    "neither"
                ],
            },
            "effectTypes": [
                "CNV"
            ]
        }
        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]
        self.assertEqual(result['effect'], 'CNV')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            365
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            6
        )
        self.assertEqual(
            result['maleResults']['negative']['count'],
            2339
        )
        self.assertEqual(
            result['maleResults']['positive']['count'],
            18
        )
