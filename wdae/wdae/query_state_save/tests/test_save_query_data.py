import json

import pytest
from rest_framework import status

from query_state_save.models import PAGE_TYPE_OPTIONS


def test_save_endpoint(query_save, simple_query_data):
    url_code = query_save(simple_query_data, "genotype")

    assert url_code != ""


@pytest.mark.parametrize("type", PAGE_TYPE_OPTIONS)
def test_load_endpoint(query_save, query_load, simple_query_data, type):
    url_code = query_save(simple_query_data, type)

    loaded = query_load(url_code)

    assert loaded["data"] == simple_query_data
    assert loaded["page"] == type


def test_invalid_page_fails(db, user_client, simple_query_data):
    url = "/api/v3/query_state/save"
    query = {"data": simple_query_data, "page": "alabala"}

    response = user_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
