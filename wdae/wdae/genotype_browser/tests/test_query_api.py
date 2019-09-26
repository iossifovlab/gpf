'''
Created on Feb 6, 2017

@author: lubo
'''
import copy
import json
import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')


EXAMPLE_REQUEST_F1 = {
    'datasetId': 'quads_f1',
}


PREVIEW_URL = '/api/v3/genotype_browser/preview'
DOWNLOAD_URL = '/api/v3/genotype_browser/download'


def test_simple_query_preview(db, admin_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)

    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 'cols' in res
    assert 'rows' in res
    assert 'count' in res
    assert 'legend' in res

    assert 8 == len(res['legend'])
    assert 2 == int(res['count'])
    assert 2 == len(res['rows'])


def test_missing_dataset(db, user_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    del data['datasetId']

    response = user_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_bad_dataset(db, user_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data['datasetId'] = 'ala bala portokala'

    response = user_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_simple_query_download(db, admin_client):
    data = {
        'queryData': json.dumps(EXAMPLE_REQUEST_F1)
    }

    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert res
    assert res[0]
    header = res[0].decode('utf-8')[:-1].split('\t')

    assert len(res) == 3

    assert header == [
        'family id', 'study', 'phenotype', 'location', 'variant',
        'family genotype', 'from parents', 'in childs', 'worst effect type',
        'genes', 'count', 'all effects', 'effect details', 'LGD rank',
        'RVIS rank', 'SSC', 'EVS', 'E65'
    ]
