import urllib.parse

import requests
from requests.auth import HTTPBasicAuth


class GPFRestClient:
    """GPF Rest Client."""

    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = f"{base_url}/o/token/"
        self.redirect_uri = redirect_uri
        self.token: str | None = None

    def authenticate(self) -> None:
        """Authenticate, second try."""
        params = [
            ("grant_type", "client_credentials"),
        ]
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        body = urllib.parse.urlencode(params)
        body = urlencode(params)

        with requests.post(
            self.token_url,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=body,
            auth=auth,
            timeout=self.DEFAULT_TIMEOUT,
        ) as response:
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to obtain token for <{self.client_id}> "
                    f"from <{self.base_url}>",
                )
        self.token = response.json()["access_token"]


def encode_params_utf8(
    params: list[tuple[str, str]],
) -> list[tuple[bytes, bytes]]:
    """Ensures that all parameters in a list of 2-element tuples are encoded to
    bytestrings using UTF-8
    """
    encoded = []
    for k, v in params:
        encoded.append((
            k.encode("utf-8") if isinstance(k, str) else k,
            v.encode("utf-8") if isinstance(v, str) else v))
    return encoded


def urlencode(params: list[tuple[str, str]]) -> str:
    utf8_params = encode_params_utf8(params)
    urlencoded = urllib.parse.urlencode(utf8_params)
    if isinstance(urlencoded, str):
        return urlencoded
    return urlencoded.decode("utf-8")
