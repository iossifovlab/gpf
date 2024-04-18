import functools
import json

import pytest
from rest_framework import status


def save_object(data, page, client):
    url = "/api/v3/query_state/save"
    query = {"data": data, "page": page}
    response = client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    return response.data.get("uuid")


def load_object(url_code, client):
    url = "/api/v3/query_state/load"
    query = {"uuid": url_code}

    response = client.post(url, query, format="json")

    assert response.status_code == status.HTTP_200_OK

    return response.data


@pytest.fixture()
def query_load(db, user_client):

    return functools.partial(load_object, client=user_client)


@pytest.fixture()
def query_save(db, user_client):
    return functools.partial(save_object, client=user_client)


@pytest.fixture()
def simple_query_data():
    return {"some": "data", "list": [1, 2, 3]}
