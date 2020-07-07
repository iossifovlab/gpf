import json
from pprint import pprint

from rest_framework import status


def test_invalid_verif_path(client, researcher):
    url = "/api/v3/users/check_verif_path"
    data = {
        "verifPath": "dasdasdasdasdsa",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_reset_pass(client, researcher):
    url = "/api/v3/users/reset_password"
    data = {"email": researcher.email}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK


def test_register_existing_user(client, researcher):
    url = "/api/v3/users/register"
    data = {
        "name": researcher.name,
        "email": researcher.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
