# pylint: disable=W0621,C0114,C0116,W0212,W0613
import html
import json
import re
from typing import cast

from django.http import HttpResponse
from django.test.client import Client
from oauth2_provider.models import AccessToken, Application
from rest_framework import status

from users_api.models import WdaeUser

LOGIN_URL = "/accounts/login"
DEFAULT_REDIRECT_URI = "http://localhost:4200/datasets"
LOGIN_PAGE_URL = "/accounts/login/"
DEFAULT_ABOUT_URI = "http://localhost:4200/about"


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


def get_about_links(
    client: Client, next_uri: str | None = None,
) -> tuple[str, str]:
    """Return the ``about`` context value and the About link of the page."""
    data = {} if next_uri is None else {"next": next_uri}
    response = client.get(LOGIN_PAGE_URL, data)
    assert response.status_code == status.HTTP_200_OK
    match = re.search(
        r'id="registration-info-link" href="([^"]*)"',
        response.content.decode(),
    )
    assert match is not None
    return response.context["about"], html.unescape(match.group(1))


def test_login_page_about_link_ignores_javascript_redirect_uri(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = (
        "/o/authorize/?redirect_uri=javascript:alert(document.cookie)//login"
    )

    about, href = get_about_links(client, next_uri)

    assert about == DEFAULT_ABOUT_URI
    assert href == DEFAULT_ABOUT_URI


def test_login_page_about_link_ignores_encoded_javascript_redirect_uri(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = (
        "/o/authorize/?redirect_uri="
        "javascript%3Aalert(document.cookie)%2F%2Flogin"
    )

    about, href = get_about_links(client, next_uri)

    assert about == DEFAULT_ABOUT_URI
    assert href == DEFAULT_ABOUT_URI


def test_login_page_about_link_ignores_unregistered_redirect_uri(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = "/o/authorize/?redirect_uri=https://evil.example/login"

    about, href = get_about_links(client, next_uri)

    assert "evil.example" not in about
    assert "evil.example" not in href


def test_login_page_about_link_follows_registered_redirect_uri(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,
) -> None:
    oauth_app.redirect_uris = (
        "http://localhost:4200/datasets http://frontend/login"
    )
    oauth_app.save()
    next_uri = "/o/authorize/?redirect_uri=http%3A%2F%2Ffrontend%2Flogin"

    about, href = get_about_links(client, next_uri)

    assert about == "http://frontend/about"
    assert href == "http://frontend/about"


def test_login_page_about_link_without_next_uses_default_app(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
    oauth_app: Application,  # ruff: ignore[unused-function-argument]
) -> None:
    about, href = get_about_links(client)

    assert about == DEFAULT_ABOUT_URI
    assert href == DEFAULT_ABOUT_URI


def test_login_page_about_link_without_default_app(
    db: None, client: Client,  # ruff: ignore[unused-function-argument]
) -> None:
    next_uri = "/o/authorize/?response_type=token&client_id=federation2"

    about, href = get_about_links(client, next_uri)

    assert about == "about"
    assert href == "about"
