# ruff: file-ignore[hardcoded-password-func-arg]
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.contrib.sessions.models import Session
from django.test.client import Client
from django.utils import timezone
from oauth2_provider.models import (
    AccessToken,
    Application,
    get_access_token_model,
    get_grant_model,
    get_refresh_token_model,
)
from rest_framework import status

from users_api.models import (
    BaseVerificationCode,
    ResetPasswordCode,
    SetPasswordCode,
    WdaeUser,
)

if TYPE_CHECKING:
    # The django-stubs type of a test client response. It exists only in
    # the stubs, so it is imported only for the type checker.
    from django.test.client import _MonkeyPatchedWSGIResponse

NEW_PASSWORD = "Unguessable-Horse-Battery-71"  # ruff: ignore[hardcoded-password-string]
USER_INFO_URL = "/api/v3/users/get_user_info"
RESET_URL = "/api/v3/users/reset_password"
SET_URL = "/api/v3/users/set_password"
DEFAULT_REDIRECT_URI = "http://localhost:4200/datasets"


def has_session(user: WdaeUser) -> bool:
    return any(
        session.get_decoded().get("_auth_user_id") == str(user.pk)
        for session in Session.objects.all()
    )


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


def complete_password_change(
    client: Client, url: str, code: BaseVerificationCode,
) -> "_MonkeyPatchedWSGIResponse":
    response = client.get(url, {"code": code.path})
    assert response.status_code == status.HTTP_200_OK
    response = client.post(
        url,
        json.dumps({
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        }),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_302_FOUND
    return response


def complete_reset(
    client: Client, user: WdaeUser,
) -> "_MonkeyPatchedWSGIResponse":
    return complete_password_change(
        client, RESET_URL, ResetPasswordCode.create(user))


@pytest.mark.django_db
def test_completed_reset_rejects_the_old_access_token(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "old-token")

    complete_reset(Client(), researcher)

    response = Client(HTTP_AUTHORIZATION="Bearer old-token").get(
        USER_INFO_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_completed_reset_leaves_no_live_token_or_grant(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    access_token = give_access_token(researcher, oauth_app, "old-token")
    get_refresh_token_model().objects.create(
        user=researcher, token="old-refresh-token",
        application=oauth_app, access_token=access_token,
    )
    get_grant_model().objects.create(
        user=researcher, code="old-grant-code", application=oauth_app,
        expires=timezone.now() + timedelta(seconds=300),
        redirect_uri="http://localhost:4200/datasets", scope="read",
    )

    complete_reset(Client(), researcher)

    assert not get_access_token_model().objects.filter(
        user=researcher).exists()
    assert not get_refresh_token_model().objects.filter(
        user=researcher, revoked__isnull=True).exists()
    assert not get_grant_model().objects.filter(user=researcher).exists()


@pytest.mark.django_db
def test_deauthenticate_deletes_the_sessions_of_the_user(
    researcher: WdaeUser,
) -> None:
    assert Client().login(email=researcher.email, password="alabala")
    assert has_session(researcher)

    researcher.deauthenticate()

    assert not has_session(researcher)


@pytest.mark.django_db
def test_deauthenticate_keeps_the_sessions_of_another_user(
    researcher: WdaeUser, user: WdaeUser,
) -> None:
    assert Client().login(email=researcher.email, password="alabala")
    assert Client().login(email=user.email, password="secret")

    researcher.deauthenticate()

    assert has_session(user)


@pytest.mark.django_db
@pytest.mark.usefixtures("oauth_app")
def test_completed_reset_ends_the_session_of_the_resetting_client(
    researcher: WdaeUser,
) -> None:
    client = Client()
    assert client.login(email=researcher.email, password="alabala")

    response = complete_reset(client, researcher)

    assert response["Location"] == DEFAULT_REDIRECT_URI
    assert not has_session(researcher)


@pytest.mark.django_db
@pytest.mark.usefixtures("oauth_app")
def test_completed_reset_keeps_the_sessions_of_another_user(
    researcher: WdaeUser, user: WdaeUser,
) -> None:
    assert Client().login(email=user.email, password="secret")

    complete_reset(Client(), researcher)

    assert has_session(user)


@pytest.mark.django_db
def test_completed_set_password_ends_the_session_and_the_tokens(
    researcher: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "old-token")
    client = Client()
    assert client.login(email=researcher.email, password="alabala")

    response = complete_password_change(
        client, SET_URL, SetPasswordCode.create(researcher))

    assert response["Location"] == DEFAULT_REDIRECT_URI
    assert not has_session(researcher)
    assert not get_access_token_model().objects.filter(
        user=researcher).exists()


@pytest.mark.django_db
def test_forgotten_password_request_keeps_the_sessions_of_the_user(
    researcher: WdaeUser,
) -> None:
    client = Client()
    assert client.login(email=researcher.email, password="alabala")

    response = client.post(
        "/api/v3/users/forgotten_password",
        json.dumps({"email": researcher.email}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert has_session(researcher)


@pytest.mark.django_db
def test_admin_password_reset_keeps_the_sessions_of_the_user(
    admin_client: Client, researcher: WdaeUser,
) -> None:
    assert Client().login(email=researcher.email, password="alabala")

    response = admin_client.post(
        f"/api/v3/users/{researcher.pk}/password_reset")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert has_session(researcher)


@pytest.mark.django_db
def test_completed_reset_keeps_the_access_token_of_another_user(
    researcher: WdaeUser, user: WdaeUser, oauth_app: Application,
) -> None:
    give_access_token(researcher, oauth_app, "old-token")
    give_access_token(user, oauth_app, "other-user-token")

    complete_reset(Client(), researcher)

    assert not get_access_token_model().objects.filter(
        user=researcher).exists()
    response = Client(HTTP_AUTHORIZATION="Bearer other-user-token").get(
        USER_INFO_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == user.email
