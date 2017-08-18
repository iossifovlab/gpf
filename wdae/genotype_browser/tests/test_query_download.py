'''
Created on Jul 11, 2017

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import copy
from rest_framework import status
import urllib
import json
EXAMPLE_REQUEST_VIP = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "VIP",
    "pedigreeSelector": {
        "id": "16pstatus",
        "checkedValues": [
            "deletion",
            "duplication",
            "triplication",
            "negative"]
    }
}


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/genotype_browser/download"

    def test_query_download_urlencoded(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_VIP)
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(64 + 1, count_iterable(response.streaming_content))

    def test_query_download_json(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_VIP)
        query = {"queryData": json.dumps(data)}

        response = self.client.post(
            self.URL, query, format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(64 + 1, count_iterable(response.streaming_content))
