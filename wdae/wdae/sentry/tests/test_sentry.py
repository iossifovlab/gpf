import os
import time
from http.cookies import SimpleCookie
from unittest import mock

from rest_framework import status


@mock.patch.dict(os.environ, {
    "WDAE_SENTRY_DSN": "https://0@0.ingest.sentry.io/0"
})
def test_sentry_token_validation(anonymous_client, mocker):
    # pylint: disable=missing-function-docstring
    mocker.patch("requests.post")

    token_time = int(time.time() * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_200_OK

    token_time = token_time - (2 * 60 * 60 * pow(10, 6))
    anonymous_client.cookies = SimpleCookie({
        "sentry_token": f"t={token_time}"
    })
    response = anonymous_client.post(
        "/api/v3/sentry", "blabla", content_type="text/plain"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
