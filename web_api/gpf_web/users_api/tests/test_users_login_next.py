# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import cast

from django.http import HttpResponse
from django.test.client import Client
from oauth2_provider.models import AccessToken, Application
from rest_framework import status

from users_api.models import WdaeUser

LOGIN_URL = "/accounts/login"
DEFAULT_REDIRECT_URI = "http://localhost:4200/datasets"


def post_login(
    client: Client, next_uri: object, *, secure: bool = False,
) -> HttpResponse:
    data = {
        "username": "user@example.com",
        "password": "secret",
        "next": next_uri,
    }
    return cast(HttpResponse, client.post(
        LOGIN_URL, json.dumps(data),
        content_type="application/json", format="json", secure=secure,
    ))


def test_login_with_next_on_other_host_redirects_to_default_app(
    db: None, user: WdaeUser, client: Client,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> None:
    response = post_login(client, "https://evil.example/")

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == DEFAULT_REDIRECT_URI


def test_login_with_next_on_redirect_uri_host_follows_next(
    db: None, user: WdaeUser, client: Client,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = "http://localhost:4200/genotype_browser"

    response = post_login(client, next_uri)

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == next_uri


def test_login_with_absolute_next_on_request_host_follows_next(
    db: None, user: WdaeUser, client: Client,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = "http://testserver/o/authorize/?x"

    response = post_login(client, next_uri)

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == next_uri


def test_secure_login_with_http_next_redirects_to_default_app(
    db: None, user: WdaeUser, client: Client,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> None:
    response = post_login(client, "http://testserver/x", secure=True)

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == DEFAULT_REDIRECT_URI


def test_login_with_non_string_next_redirects_to_default_app(
    db: None, user: WdaeUser, client: Client,  # ruff: ignore[unused-function-argument]
    tokens: tuple[AccessToken, AccessToken],  # ruff: ignore[unused-function-argument]
) -> None:
    response = post_login(client, ["/x"])

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == DEFAULT_REDIRECT_URI


def test_login_page_drops_next_on_other_host(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,  # ruff: ignore[unused-function-argument]
) -> None:
    response = client.get(f"{LOGIN_URL}?next=https://evil.example/")

    assert response.status_code == status.HTTP_200_OK
    assert b"evil.example" not in response.content
