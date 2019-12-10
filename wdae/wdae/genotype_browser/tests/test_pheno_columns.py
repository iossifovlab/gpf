import pytest

import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')

PREVIEW_URL = '/api/v3/genotype_browser/preview'
PREVIEW_VARIANTS_URL = '/api/v3/genotype_browser/preview/variants'


def test_simple_query_preview(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type='application/json'
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads(''.join(map(lambda x: x.decode('utf-8'), res)))

    assert 2 == len(res)


def test_query_preview_have_pheno_columns(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json'
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 20 == len(res['cols'])
    assert res['cols'][-4:] == [
        'continuous.Continuous',
        'categorical.Categorical',
        'ordinal.Ordinal',
        'raw.Raw'
    ]


def test_query_preview_have_pheno_column_values(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type='application/json'
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads(''.join(map(lambda x: x.decode('utf-8'), res)))

    assert len(res) == 2
    for row in enumerate(res):
        for value in row[-4:]:
            assert value is not None
