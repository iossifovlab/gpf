# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest

from federation.rest_api_client import RESTClient
from rest_client.rest_client import GPFConfidentialClient


@pytest.fixture
def remote_config() -> dict[str, str]:
    host = os.environ.get("TEST_REMOTE_HOST", "localhost")
    return {
        "id": "TEST_REMOTE",
        "host": host,
        "protocol": "http",
        "port": "21010",
        "client_id": "federation",
        "client_secret": "secret",
    }


@pytest.fixture
def rest_client(remote_config: dict[str, str]) -> RESTClient:
    client = RESTClient(
        remote_config["id"],
        remote_config["host"],
        remote_config["client_id"],
        remote_config["client_secret"],
        protocol=remote_config["protocol"],
        port=int(remote_config["port"]),
    )

    assert isinstance(client.gpf_rest_client.session,
                      GPFConfidentialClient)
    assert client.gpf_rest_client.session.token is not None, \
        "Failed to get auth token for REST client"

    return client
