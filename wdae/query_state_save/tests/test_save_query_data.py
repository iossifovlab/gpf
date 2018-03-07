import functools
import pytest
from rest_framework import status
from query_state_save.models import PAGE_TYPE_OPTIONS


def save_object(data, page, save_endpoint, client):
    response = client.post(save_endpoint, {
        "data": data,
        "page": page
    }, format="json")

    assert response.status_code == status.HTTP_201_CREATED

    return response.data.get("uuid")


def load_object(url_code, load_endpoint, client):
    response = client.post(load_endpoint, {
        "uuid": url_code
    }, format="json")

    assert response.status_code == status.HTTP_200_OK

    return response.data


@pytest.fixture()
def query_load(db, load_endpoint, client):

    return functools.partial(
        load_object, load_endpoint=load_endpoint, client=client)


@pytest.fixture()
def query_save(db, save_endpoint, client):

    return functools.partial(
        save_object, save_endpoint=save_endpoint, client=client)


@pytest.fixture()
def simple_query_data():
    return {
        "some": "data",
        "list": [1, 2, 3]
    }


def test_save_endpoint(query_save, simple_query_data):
    url_code = query_save(simple_query_data, "genotype")

    assert url_code != ""


@pytest.mark.parametrize("type", PAGE_TYPE_OPTIONS)
def test_load_endpoint(query_save, query_load, simple_query_data, type):
    url_code = query_save(simple_query_data, type)

    loaded = query_load(url_code)

    assert loaded["data"] == simple_query_data
    assert loaded["page"] == type


def test_invalid_page_fails(db, client, save_endpoint, simple_query_data):
    response = client.post(
        save_endpoint,
        {
            "data": simple_query_data,
            "page": "alabala"
        },
        format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
