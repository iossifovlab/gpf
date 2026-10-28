# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import logging

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test.client import Client
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from utils.logger import log_filter

from users_api.models import ResetPasswordCode, WdaeUser

SECRET_DATA = {
    "password": "secret-password-value",
    "new_password1": "secret-new-password-one",
    "new_password2": "secret-new-password-two",
    "code": "secret-code-value",
    "verifPath": "secret-verif-path-value",
    "token": "secret-token-value",
    "oldPassword": "secret-old-password-value",
}


def make_request(data: dict[str, str]) -> Request:
    wsgi_request = APIRequestFactory().post(
        "/api/v3/users/some_view", data, format="json",
    )
    request = Request(wsgi_request, parsers=[JSONParser()])
    request.user = AnonymousUser()
    return request


def test_log_filter_masks_secret_keys_in_data() -> None:
    request = make_request({**SECRET_DATA, "email": "plain-email-value"})

    line = log_filter(request, "message")

    for secret in SECRET_DATA.values():
        assert secret not in line
    assert "plain-email-value" in line


@pytest.mark.usefixtures("tokens")
def test_reset_password_log_holds_no_code_and_no_password(
    client: Client, researcher: WdaeUser, caplog: pytest.LogCaptureFixture,
) -> None:
    code = ResetPasswordCode.create(researcher)
    new_password = "logged-never-password"  # ruff: ignore[hardcoded-password-string]

    with caplog.at_level(logging.INFO):
        client.get(f"/api/v3/users/reset_password?code={code.path}")
        client.post(
            "/api/v3/users/reset_password",
            json.dumps({
                "new_password1": new_password,
                "new_password2": new_password,
            }),
            content_type="application/json",
        )

    researcher.refresh_from_db()
    assert researcher.check_password(new_password)
    assert str(code.path) not in caplog.text
    assert new_password not in caplog.text


def test_forgotten_password_log_holds_no_reset_code(
    client: Client, researcher: WdaeUser, caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        client.post(
            "/api/v3/users/forgotten_password",
            json.dumps({"email": researcher.email}),
            content_type="application/json",
        )

    code = ResetPasswordCode.objects.get(user=researcher)
    assert str(code.path) not in caplog.text


@pytest.mark.usefixtures("db")
def test_change_password_log_holds_no_refused_password(
    client: Client, caplog: pytest.LogCaptureFixture,
) -> None:
    refused_password = "wkpw-x7q"  # ruff: ignore[hardcoded-password-string]

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v3/users/change_password",
            json.dumps({
                "password": refused_password,
                "verifPath": "some-verif-path",
            }),
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid password" in caplog.text
    assert refused_password not in caplog.text
