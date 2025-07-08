# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from oauthlib.oauth2 import (
    BackendApplicationClient,
    MobileApplicationClient,
)
from requests_oauthlib import OAuth2Session


def test_oauth2_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    auth_url = "http://localhost:21010/o/authorize/"

    with monkeypatch.context() as m:
        m.setenv("OAUTHLIB_INSECURE_TRANSPORT", "yes")

        client = MobileApplicationClient(
            client_id="federation2",
            redirect_url="http://localhost:21010/login",
        )

        oauth = OAuth2Session(
            client=client,
            pkce="S256",
            state="1",
        )
        authorization_url, _state = oauth.authorization_url(
            auth_url, state="1",
        )

        with oauth.get(authorization_url) as response:
            assert response.status_code == 200


def test_oauth2_confidential_client(monkeypatch: pytest.MonkeyPatch) -> None:
    token_url = "http://localhost:21010/o/token/"  # noqa: S105

    with monkeypatch.context() as m:
        m.setenv("OAUTHLIB_INSECURE_TRANSPORT", "yes")

        client_id = "federation"
        client_secret = "secret"  # noqa: S105

        client = BackendApplicationClient(
            client_id=client_id,
            redirect_url="http://localhost:21010/login",
        )

        oauth = OAuth2Session(
            client=client,
        )

        token = oauth.fetch_token(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
        )

        assert token
