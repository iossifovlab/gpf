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
    VIP_QUERY = {
        "datasetId": "VIP",
        "measureId": "treatment_history.age_ended",
        "normalizeBy": [
            "age",
            "non-verbal iq"
        ],
        "presentInParent": {
            "presentInParent": [
                "neither"
            ],
        },
        "effectTypes": [
            'LGDs'
        ]
    }

    def test_vip_treatment_history(self):
        query = copy.deepcopy(self.VIP_QUERY)

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        description = response.data['description']
        self.assertEquals(
            description,
            "treatment_history.age_ended ~ "
            "diagnosis_summary.best_nonverbal_iq")

    SSC_QUERY = {
        "datasetId": "SSC",
        "measureId": "ssc_hwhc.head_circumference",
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

    def test_ssc_head_circumference(self):
        query = copy.deepcopy(self.SSC_QUERY)

        response = self.client.post(self.TOOL_URL, query, format="json")
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        description = response.data['description']
        self.assertEquals(
            description,
            'ssc_hwhc.head_circumference ~ '
            'pheno_common.age + '
            'pheno_common.non_verbal_iq'
        )
