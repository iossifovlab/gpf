# ruff: file-ignore[hardcoded-password-func-arg]
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import base64
import json
from datetime import timedelta

import pytest
from django.test.client import Client
from django.utils import timezone
from oauth2_provider.models import (
    AccessToken,
    Application,
    get_access_token_model,
    get_refresh_token_model,
)
from rest_framework import status

from users_api.models import WdaeUser

USER_INFO_URL = "/api/v3/users/get_user_info"


def give_access_token(
    user: WdaeUser, app: Application, token: str,
) -> AccessToken:
    access_token = get_access_token_model()(
        user=user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token=token,
        application=app,
    )
    access_token.save()
    return access_token


@pytest.mark.django_db
def test_token_of_an_inactive_user_is_rejected(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "researcher-token")
    researcher.is_active = False
    researcher.save()

    response = Client(HTTP_AUTHORIZATION="Bearer researcher-token").get(
        USER_INFO_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def get_federation_token(admin_client: Client) -> str:
    credentials_res = admin_client.post(
        "/api/v3/users/federation_credentials",
        json.dumps({"name": "federation-app"}),
        content_type="application/json",
    )
    assert credentials_res.status_code == status.HTTP_200_OK
    data = credentials_res.json()
    credentials = base64.b64encode(
        f"{data['client_id']}:{data['client_secret']}".encode(),
    ).decode()
    token_res = Client().post(
        "/o/token/",
        headers={"Authorization": f"Basic {credentials}"},
        data="grant_type=client_credentials",
        content_type="application/x-www-form-urlencoded",
    )
    assert token_res.status_code == status.HTTP_200_OK
    return str(token_res.json()["access_token"])


@pytest.mark.django_db
def test_federation_token_of_an_inactive_owner_is_rejected(
    admin_client: Client, admin: WdaeUser,
) -> None:
    federation_token = get_federation_token(admin_client)
    admin.is_active = False
    admin.save()
    client = Client(HTTP_AUTHORIZATION=f"Bearer {federation_token}")

    users_response = client.get("/api/v3/users")
    credentials_response = client.get("/api/v3/users/federation_credentials")

    assert users_response.status_code == status.HTTP_403_FORBIDDEN
    assert credentials_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_logout_revokes_the_token_of_the_request(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "researcher-token")
    client = Client(HTTP_AUTHORIZATION="Bearer researcher-token")

    logout_response = client.post("/api/v3/users/logout")

    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(USER_INFO_URL).status_code == \
        status.HTTP_401_UNAUTHORIZED
    assert not get_access_token_model().objects.filter(
        token="researcher-token").exists()


@pytest.mark.django_db
def test_logout_without_a_token_flushes_the_session(
    researcher: WdaeUser,
) -> None:
    client = Client()
    client.force_login(researcher)

    logout_response = client.post("/api/v3/users/logout")

    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert "_auth_user_id" not in client.session
    assert client.get(USER_INFO_URL).json()["loggedIn"] is False


@pytest.mark.django_db
def test_logout_revokes_the_refresh_token_of_the_request_token(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    access_token = give_access_token(
        researcher, oauth_app, "researcher-token")
    get_refresh_token_model().objects.create(
        user=researcher, token="researcher-refresh-token",
        application=oauth_app, access_token=access_token,
    )

    Client(HTTP_AUTHORIZATION="Bearer researcher-token").post(
        "/api/v3/users/logout")

    refresh_token = get_refresh_token_model().objects.get(
        token="researcher-refresh-token")
    assert refresh_token.revoked is not None


@pytest.mark.django_db
def test_logout_keeps_another_token_of_the_user(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "first-token")
    give_access_token(researcher, oauth_app, "second-token")

    logout_response = Client(HTTP_AUTHORIZATION="Bearer first-token").post(
        "/api/v3/users/logout")

    response = Client(HTTP_AUTHORIZATION="Bearer second-token").get(
        USER_INFO_URL)
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert not get_access_token_model().objects.filter(
        token="first-token").exists()
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == researcher.email
