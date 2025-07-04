# pylint: disable=W0621,C0114,C0116,W0212,W0613
from rest_client.rest_client import GPFOAuthSession


def test_authenticate() -> None:
    """Test authenticate simple."""
    client = GPFOAuthSession(
        base_url="http://resttest:21011",
        client_id="resttest1",
        client_secret="secret",  # noqa: S106
        redirect_uri="http://resttest:21011/login",
    )

    client.authenticate()


def test_authenticate_and_revoke() -> None:
    """Test authenticate simple."""
    client = GPFOAuthSession(
        base_url="http://resttest:21011",
        client_id="resttest1",
        client_secret="secret",  # noqa: S106
        redirect_uri="http://resttest:21011/login",
    )

    client.authenticate()
    assert client.token is not None

    client.revoke_token()
    assert client.token is None
