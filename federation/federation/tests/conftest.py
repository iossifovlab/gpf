# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest
import pytest_mock
import yaml
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from utils.testing import setup_t4c8_instance

from federation.remote_extension import GPFRemoteExtension
from federation.rest_api_client import RESTClient
from rest_client.rest_client import GPFOAuthSession


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
                      GPFOAuthSession)
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


@pytest.fixture(scope="session")
def test_remote_extension(
    t4c8_instance: WGPFInstance) -> GPFRemoteExtension:
    return t4c8_instance.extensions.get("remote_extension")


@pytest.fixture
def t4c8_wgpf_instance(
    t4c8_instance: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:

    query_transformer = QueryTransformer(
        t4c8_instance.gene_scores_db,
        t4c8_instance.reference_genome.chromosomes,
        t4c8_instance.reference_genome.chrom_prefix,
    )

    response_transformer = ResponseTransformer(
        t4c8_instance.gene_scores_db,
    )

    reload_datasets(t4c8_instance)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_query_transformer",
        return_value=query_transformer,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_response_transformer",
        return_value=response_transformer,
    )
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=t4c8_instance,
    )

    return t4c8_instance
