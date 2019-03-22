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


