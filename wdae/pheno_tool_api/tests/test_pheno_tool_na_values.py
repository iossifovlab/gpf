'''
Created on Jul 7, 2017

@author: lubo
'''
from __future__ import print_function
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from rest_framework import status
import copy


class Test(BaseAuthenticatedUserTest):

    TOOL_URL = "/api/v3/pheno_tool"
    QUERY = {
        "datasetId": "SSC",
        "measureId": "ssc_core_descriptive.ssc_diagnosis_nonverbal_iq",
        "normalizeBy": [
            "age",
            "non-verbal iq"
        ],
        "geneSymbols": [
            "POGZ"
        ],
        "presentInParent": {
            "presentInParent": [
                "neither"
            ],
        },
        "effectTypes": [
            "LGDs",
        ]
    }

    def test_simple_query_lgds(self):
        query = copy.deepcopy(self.QUERY)
        query['effectTypes'] = ['LGDs']

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]

        self.assertEqual(result['effect'], 'LGDs')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            374
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['deviation'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['mean'],
            result['femaleResults']['negative']['mean'],
        )

    def test_simple_query_missense(self):
        query = copy.deepcopy(self.QUERY)
        query['effectTypes'] = ['Missense']

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]

        self.assertEqual(result['effect'], 'Missense')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            374
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['deviation'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['mean'],
            result['femaleResults']['negative']['mean'],
        )

    def test_simple_query_synonymous(self):
        query = copy.deepcopy(self.QUERY)
        query['effectTypes'] = ['Synonymous']

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]

        self.assertEqual(result['effect'], 'Synonymous')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            374
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['deviation'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['mean'],
            result['femaleResults']['negative']['mean'],
        )

    def test_simple_query_cnv(self):
        query = copy.deepcopy(self.QUERY)
        query['effectTypes'] = ['CNV']

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = response.data['results'][0]

        self.assertEqual(result['effect'], 'CNV')
        self.assertEqual(
            result['femaleResults']['negative']['count'],
            374
        )
        self.assertEqual(
            result['femaleResults']['positive']['count'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['deviation'],
            0
        )
        self.assertEqual(
            result['femaleResults']['positive']['mean'],
            result['femaleResults']['negative']['mean'],
        )
