# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest
import yaml
from gpf_instance.gpf_instance import WGPFInstance
from utils.testing import setup_t4c8_instance

from federation.rest_api_client import RESTClient
from rest_client.rest_client import GPFConfidentialClient


def build_remote_config() -> dict[str, str]:
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
def rest_client() -> RESTClient:
    remote_config = build_remote_config()
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


@pytest.fixture(scope="session")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    instance = setup_t4c8_instance(root_path)

    with open(instance.dae_config_path, "a") as f:
        f.write(yaml.dump({"remotes": [build_remote_config()]}))

    return WGPFInstance.build(instance.dae_config_path, grr=instance.grr)
