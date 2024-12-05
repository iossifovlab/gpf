from rest_client.rest_client import GPFRestClient


def test_authenticate_urlencode() -> None:
    """Test authenticate simple."""
    client = GPFRestClient(
        base_url="http://resttest:21011",
        client_id="resttest1",
        client_secret="secret",  # noqa: S106
        redirect_uri="http://resttest:21011/login",
    )

    client.authenticate()
