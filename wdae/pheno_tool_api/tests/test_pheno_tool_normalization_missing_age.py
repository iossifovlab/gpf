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
        "datasetId": "SVIP",
        "measureId": "treatment_history.age_ended",
        "normalizeBy": [
            "age"
        ],
        "presentInParent": {
            "presentInParent": [
                "neither"
            ],
        },
        "effectTypes": [
        ]
    }

    def test_simple_query_lgds(self):
        query = copy.deepcopy(self.QUERY)
        query['effectTypes'] = ['LGDs']

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
