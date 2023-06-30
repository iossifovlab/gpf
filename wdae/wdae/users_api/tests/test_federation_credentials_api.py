# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from pprint import pprint

from rest_framework import status  # type: ignore
from oauth2_provider.models import get_application_model  # type: ignore

from utils.email_regex import email_regex, is_email_valid
from utils.password_requirements import is_password_valid


def test_create_federation_credentials_with_unauthorized_user(db, anonymous_client):
    url = "/api/v3/users/federation_credentials"
    body = {
        "name": "name1"
    }
    createRes = anonymous_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )
    assert createRes.status_code is status.HTTP_401_UNAUTHORIZED
    assert createRes.data is None
    assert get_application_model().objects.filter(name="name1").exists() is False


def test_create_duplicate_name_federation_credentials(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    createRes = user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )
    assert createRes.status_code is status.HTTP_200_OK

    createDuplicateRes = user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )
    assert createDuplicateRes.status_code is status.HTTP_400_BAD_REQUEST

    response = user_client.get(url)
    
    assert len(response.data) == 1
    assert str(response.data) == "[{'name': 'name1'}]"
    assert len(get_application_model().objects.filter(name="name1")) == 1


def test_create_federation_credentials_with_authorized_user(db, user_client):
    url = "/api/v3/users/federation_credentials"
    body = {
        "name": "name1"
    }
    credentials_res = user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert credentials_res.status_code is status.HTTP_200_OK
    assert get_application_model().objects.filter(name="name1").exists() is True

    token_res = user_client.post(
        "/o/token/",
        headers={"Authorization": f"Basic {credentials_res.data['credentials'].decode()}"},
        data={"grant_type": "client_credentials"},
        content_type="application/json", format="json"
    )
    assert token_res.status_code is status.HTTP_200_OK
    assert token_res.json().get("access_token") is not None


def test_get_federation_credentials_with_unauthorized_user(anonymous_client):
    url = "/api/v3/users/federation_credentials"
    response = anonymous_client.get(url)

    assert response.data is None
    assert response.status_code is status.HTTP_401_UNAUTHORIZED


def test_get_federation_credentials_with_authorized_user(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = { "name": "name2" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    response = user_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert str(response.data) == "[{'name': 'name1'}, {'name': 'name2'}]"


def test_update_federation_credentials_with_unauthorized_user(db, user_client, anonymous_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name1",
        "new_name": "name2"
    }
    response = anonymous_client.put(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert response.data is None
    assert response.status_code is status.HTTP_401_UNAUTHORIZED
    assert get_application_model().objects.filter(name="name1").exists() is True


def test_update_federation_credentials_with_false_name(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name2",
        "new_name": "name3"
    }
    responseWithoutNameRes = user_client.put(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert responseWithoutNameRes.data is None
    assert responseWithoutNameRes.status_code is status.HTTP_400_BAD_REQUEST
    assert get_application_model().objects.filter(name="name1").exists() is True


def test_update_federation_credentials_with_duplicate_name(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )
    body = { "name": "name2" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name1",
        "new_name": "name2",
    }
    responseWithoutNewNameRes = user_client.put(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert responseWithoutNewNameRes.data is None
    assert responseWithoutNewNameRes.status_code is status.HTTP_400_BAD_REQUEST
    assert get_application_model().objects.filter(name="name1").exists() is True
    assert get_application_model().objects.filter(name="name2").exists() is True


def test_update_federation_credentials_with_authorized_user(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )
    body = { "name": "name2" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name1",
        "new_name": "name3",
    }
    responseWithoutNewNameRes = user_client.put(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert responseWithoutNewNameRes.status_code is status.HTTP_200_OK
    assert str(responseWithoutNewNameRes.data) == "{'new_name': 'name3'}"
    assert get_application_model().objects.filter(name="name1").exists() is False
    assert get_application_model().objects.filter(name="name3").exists() is True


def test_delete_federation_credentials_with_unauthorized_user(db, user_client, anonymous_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name1",
    }
    response = anonymous_client.delete(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert response.data is None
    assert response.status_code is status.HTTP_401_UNAUTHORIZED
    assert get_application_model().objects.filter(name="name1").exists() is True


def test_delete_absent_federation_credentials(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = {
        "name": "name1",
    }
    response = user_client.delete(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert response.data is None
    assert response.status_code is status.HTTP_400_BAD_REQUEST


def test_delete_federation_credentials_with_authorized_user(db, user_client):
    url = "/api/v3/users/federation_credentials"

    body = { "name": "name1" }
    user_client.post(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    body = {
        "name": "name1",
    }
    response = user_client.delete(
        url, json.dumps(body), content_type="application/json", format="json"
    )

    assert response.status_code is status.HTTP_200_OK
    assert get_application_model().objects.filter(name="name1").exists() is False
