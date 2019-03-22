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
    "datasetId": "quads_f1",
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
    assert 4 == int(res['count'])
    assert 4 == len(res['rows'])


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
