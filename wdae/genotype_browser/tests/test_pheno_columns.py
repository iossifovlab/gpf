import pytest

import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures("mock_studies_manager")

URL = "/api/v3/genotype_browser/preview"


def test_simple_query_preview(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 4 == len(res['rows'])


def test_query_preview_have_pheno_columns(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 19 == len(res['cols'])
    assert res['cols'][-4:] == [
        'prb.instrument1.continuous',
        'prb.instrument1.categorical',
        'prb.instrument1.ordinal',
        'prb.instrument1.raw'
    ]


def test_query_preview_have_pheno_column_values(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert len(res['rows']) == 4
    for row in enumerate(res['rows']):
        for value in row[-4:]:
            assert value is not None
