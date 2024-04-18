# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from pprint import pprint

import pytest
from django.test.client import Client
from oauth2_provider.models import AccessToken
from rest_framework import status

from users_api.models import SetPasswordCode, WdaeUser

# @pytest.mark.skip
# def test_fail_register(client):
#     url = "/api/v3/users/register"
#     data = {
#         "email": "faulthymail@faulthy.com",
#         "name": "bad_name",
#     }

#     response = client.post(
#         url, json.dumps(data), content_type="application/json", format="json"
#     )
#     assert response.status_code == status.HTTP_201_CREATED


# @pytest.mark.skip
# def test_fail_register_case_changed_email(client):
#     url = "/api/v3/users/register"
#     data = {
#         "email": "FaKe@fake.com",
#         "name": "ok name",
#     }

#     response = client.post(
#         url, json.dumps(data), content_type="application/json", format="json"
#     )
#     assert response.status_code == status.HTTP_201_CREATED


def test_fail_register_wrong_id(
    client: Client,
    researcher_without_password: WdaeUser,
) -> None:
    url = "/api/v3/users/register"
    data = {
        "email": researcher_without_password.email,
        "name": "ok name",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


# @pytest.mark.skip
# def test_fail_register_wrong_email(client):
#     url = "/api/v3/users/register"
#     data = {
#         "email": "bad@email.com",
#         "name": "ok name",
#     }

#     response = client.post(
#         url, json.dumps(data), content_type="application/json", format="json"
#     )
#     assert response.status_code == status.HTTP_201_CREATED


def test_reset_pass_without_registration(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    url = "/api/v3/users/forgotten_password"
    data = {"email": researcher_without_password.email}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db()
def test_reset_pass_without_registration_wrong_email(
    client: Client,
) -> None:
    url = "/api/v3/users/forgotten_password"
    data = {"email": "wrong@email.com"}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_successful_register(
    client: Client,
    researcher_without_password: WdaeUser,
) -> None:
    name = "NEW_NAME"
    url = "/api/v3/users/register"
    data = {
        "name": name,
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    user = WdaeUser.objects.get(email=researcher_without_password.email)
    assert user.name == name


def test_successful_register_empty_name(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    old_name = researcher_without_password.name
    url = "/api/v3/users/register"
    data = {"name": "", "email": researcher_without_password.email}
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    user = WdaeUser.objects.get(email=researcher_without_password.email)
    assert user.name == old_name


def test_successful_register_missing_name(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    old_name = researcher_without_password.name
    url = "/api/v3/users/register"
    data = {
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    user = WdaeUser.objects.get(email=researcher_without_password.email)
    assert user.name == old_name


def test_register_twice(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    url = "/api/v3/users/register"
    data = {
        "name": researcher_without_password.name,
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_registration_all_steps(
    client: Client, researcher_without_password: WdaeUser,
    tokens: tuple[AccessToken, AccessToken],
) -> None:
    url = "/api/v3/users/register"
    data = {
        "name": researcher_without_password.name,
        "email": researcher_without_password.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    code = SetPasswordCode.get_code(researcher_without_password)

    assert code is not None

    url = "/api/v3/users/set_password"
    session = client.session
    session.update({"set_code": code.path})
    session.save()
    data = {
        "new_password1": "samplenewpassword",
        "new_password2": "samplenewpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_302_FOUND

    url = "/accounts/login"
    data = {
        "username": researcher_without_password.email,
        "password": "samplenewpassword",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_302_FOUND
