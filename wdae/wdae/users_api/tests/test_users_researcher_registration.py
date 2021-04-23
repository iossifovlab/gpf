import pytest
import json
from pprint import pprint

from rest_framework import status

from users_api.models import WdaeUser


@pytest.mark.skip
def test_fail_register(client):
    url = "/api/v3/users/register"
    data = {
        "email": "faulthymail@faulthy.com",
        "name": "bad_name",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.skip
def test_fail_register_case_changed_email(client):
    url = "/api/v3/users/register"
    data = {
        "email": "FaKe@fake.com",
        "name": "ok name",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_fail_register_wrong_id(client, researcher_without_password):
    url = "/api/v3/users/register"
    data = {
        "email": researcher_without_password.email,
        "name": "ok name",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.skip
def test_fail_register_wrong_email(client):
    url = "/api/v3/users/register"
    data = {
        "email": "bad@email.com",
        "name": "ok name",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_reset_pass_without_registration(client, researcher_without_password):
    url = "/api/v3/users/reset_password"
    data = {"email": researcher_without_password.email}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK


def test_reset_pass_without_registration_wrong_email(db, client):
    url = "/api/v3/users/reset_password"
    data = {"email": "wrong@email.com"}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK


def test_successful_register(client, researcher_without_password):
    name = "NEW_NAME"
    url = "/api/v3/users/register"
    data = {
        "name": name,
        "email": researcher_without_password.email
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    u = WdaeUser.objects.get(email=researcher_without_password.email)
    assert u.name == name


def test_successful_register_empty_name(client, researcher_without_password):
    old_name = researcher_without_password.name
    url = "/api/v3/users/register"
    data = {"name": "", "email": researcher_without_password.email}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    u = WdaeUser.objects.get(email=researcher_without_password.email)
    assert u.name == old_name


def test_successful_register_missing_name(client, researcher_without_password):
    old_name = researcher_without_password.name
    url = "/api/v3/users/register"
    data = {
        "email": researcher_without_password.email
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    u = WdaeUser.objects.get(email=researcher_without_password.email)
    assert u.name == old_name


def test_register_twice(client, researcher_without_password):
    url = "/api/v3/users/register"
    data = {
        "name": researcher_without_password.name,
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_registration_all_steps(client, researcher_without_password):
    url = "/api/v3/users/register"
    data = {
        "name": researcher_without_password.name,
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    verifPath = researcher_without_password.verificationpath.path

    url = "/api/v3/users/check_verif_path"
    data = {
        "verifPath": verifPath,
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK

    url = "/api/v3/users/change_password"
    data = {"verifPath": verifPath, "password": "testpassword"}
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    url = "/api/v3/users/login"
    data = {
        "username": researcher_without_password.email,
        "password": "testpassword",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
