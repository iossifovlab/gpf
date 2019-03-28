import pytest
import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures("mock_studies_manager")

URL = "/api/v3/genotype_browser/preview"


def test_variants_have_roles_columns(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 'inChS' in res['cols']
    assert 'fromParentS' in res['cols']


def test_variants_have_roles_columns_values(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    in_child_index = res['cols'].index('inChS')
    from_parents_index = res['cols'].index('fromParentS')

    in_child_expected = ['', 'prbM', '', 'prbM']
    from_parents_expected = ['', 'momF', '', 'dadM']

    for i, row in enumerate(res['rows']):
        assert row[in_child_index] == in_child_expected[i], i
        assert row[from_parents_index] == from_parents_expected[i], i
