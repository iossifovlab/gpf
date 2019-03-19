'''
Created on Feb 6, 2017

@author: lubo
'''
import copy
import json
import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures("mock_studies_manager")


EXAMPLE_REQUEST_F1 = {
    "datasetId": "inheritance_trio",
    # "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    # "gender": ["female", "male"],
    # "presentInChild": [
    #     "affected and unaffected",
    #     "affected only",
    # ],
    # "presentInParent": [
    #     "neither",
    # ],
    # "variantTypes": [
    #     "CNV", "del", "ins", "sub",
    # ],
    # "pedigreeSelector": {
    #     "id": "phenotype",
    #     "checkedValues": ["autism", "unaffected"]
    # }
}


URL = "/api/v3/genotype_browser/preview"


def test_simple_query_preview(db, admin_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)

    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 'cols' in res
    assert 'rows' in res
    assert 'count' in res
    assert 'legend' in res

    assert 8 == len(res['legend'])
    # self.assertEquals(422, int(res['count']))
    assert 28 == int(res['count'])
    # self.assertEquals(422, len(res['rows']))
    assert 28 == len(res['rows'])


def test_missing_dataset(db, client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    del data['datasetId']

    response = client.post(URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_bad_dataset(db, client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data['datasetId'] = 'ala bala portokala'

    response = client.post(URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code
