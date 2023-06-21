import os
import time
from http.cookies import SimpleCookie
from unittest import mock

from rest_framework import status


def test_sentry_missing_env(anonymous_client, mocker):
    # pylint: disable=missing-function-docstring
    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0"
})
def test_sentry_missing_cookie(anonymous_client, mocker):
    # pylint: disable=missing-function-docstring
    requests_mock = mocker.patch("requests.post")

    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0"
})
def test_sentry_invalid_cookie(anonymous_client, mocker):
    # pylint: disable=missing-function-docstring
    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() - (2 * 60 * 60)) * pow(10, 6)
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    requests_mock.assert_not_called()


@mock.patch.dict(os.environ, {
    "GPFJS_SENTRY_DSN": "https://0@0.ingest.sentry.io/0"
})
def test_sentry_valid_cookie(anonymous_client, mocker):
    # pylint: disable=missing-function-docstring
    requests_mock = mocker.patch("requests.post")

    token_time = int(time.time() * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_200_OK
    requests_mock.assert_called_once()

    token_time = token_time - (2 * 60 * 60 * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    requests_mock.assert_called_once()
