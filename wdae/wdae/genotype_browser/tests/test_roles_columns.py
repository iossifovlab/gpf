import pytest
import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')

PREVIEW_URL = '/api/v3/genotype_browser/preview'
DOWNLOAD_URL = '/api/v3/genotype_browser/download'


def test_variants_have_roles_columns(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 'genotype.in child' in res['cols']
    assert 'genotype.from parent' in res['cols']


def test_variants_have_roles_columns_values(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    in_child_index = res['cols'].index('genotype.in child')
    from_parents_index = res['cols'].index('genotype.from parent')

    in_child_expected = ['prbM', 'prbM']
    from_parents_expected = ['momF', 'dadM']

    print('in_child_expected:', in_child_expected)

    for i, row in enumerate(res['rows']):
        print('row:', row[in_child_index])
        assert row[in_child_index] == in_child_expected[i], i
        assert row[from_parents_index] == from_parents_expected[i], i


def test_download_variants_have_roles_columns(db, admin_client):
    data = {
        'queryData': '{"datasetId": "quads_f1"}'
    }

    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert res
    assert res[0]
    header = res[0].decode('utf-8')[:-1].split('\t')

    assert 'in childs' in header
    assert 'from parents' in header
