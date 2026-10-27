# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import os
import time
from http.cookies import SimpleCookie
from unittest import mock

import pytest
import pytest_mock
import requests
from django.conf import settings
from django.test import Client
from rest_framework import status


def test_sentry_missing_env(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}",
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_missing_cookie(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_invalid_cookie(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:

    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() - (2 * 60 * 60)) * pow(10, 6)
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}",
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_valid_cookie(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}",
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_called_once()

    token_time = token_time - (2 * 60 * 60 * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}",
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    requests_mock.assert_called_once()


def _token(offset: float = 0) -> str:
    """Return a sentry token issued ``offset`` seconds from now."""
    return f"t={int((time.time() + offset) * pow(10, 6))}"


@pytest.mark.parametrize("sentry_token", [
    "t=nan",
    "t=inf",
    "t=-inf",
    "garbage",
    "t=abc",
    _token(2 * 60 * 60),
], ids=["nan", "inf", "-inf", "no-equals", "not-a-number", "future"])
@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_unreadable_or_future_token_is_unauthorized(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
    sentry_token: str,
) -> None:
    requests_mock = mocker.patch("requests.post")
    anonymous_client.cookies = SimpleCookie({"sentry_token": sentry_token})

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_body_over_upload_limit_is_rejected(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")
    anonymous_client.cookies = SimpleCookie({"sentry_token": _token()})
    body = "x" * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1)

    response = anonymous_client.post(
        "/api/v3/sentry", body, content_type="text/plain",
    )

    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_upstream_call_uses_short_timeout(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")
    anonymous_client.cookies = SimpleCookie({"sentry_token": _token()})

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )

    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_called_once()
    assert requests_mock.call_args.kwargs["timeout"] == 5


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_body_over_upload_limit_without_cookie_is_ok(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
) -> None:
    requests_mock = mocker.patch("requests.post")
    body = "x" * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1)

    response = anonymous_client.post(
        "/api/v3/sentry", body, content_type="text/plain",
    )

    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_not_called()


@pytest.mark.parametrize("offset,expected_status,expected_calls", [
    (30, status.HTTP_200_OK, 1),
    (120, status.HTTP_401_UNAUTHORIZED, 0),
], ids=["within-skew", "beyond-skew"])
@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_future_token_clock_skew_bound(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
    offset: int, expected_status: int, expected_calls: int,
) -> None:
    requests_mock = mocker.patch("requests.post")
    anonymous_client.cookies = SimpleCookie({"sentry_token": _token(offset)})

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )

    assert response.status_code == expected_status
    assert requests_mock.call_count == expected_calls


@pytest.mark.parametrize("error", [
    requests.exceptions.Timeout("timed out"),
    requests.exceptions.ConnectionError("unreachable"),
], ids=["timeout", "connection-error"])
@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0",
})
def test_sentry_upstream_failure_is_bad_gateway(
    anonymous_client: Client, mocker: pytest_mock.MockerFixture,
    error: requests.RequestException,
) -> None:
    requests_mock = mocker.patch("requests.post", side_effect=error)
    anonymous_client.cookies = SimpleCookie({"sentry_token": _token()})

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain",
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    requests_mock.assert_called_once()
