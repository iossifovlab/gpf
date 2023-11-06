# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_datasets_api_get_remote_studies(
    admin_client: Client
) -> None:
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200

    data = response.json()["data"]

    assert any(map(lambda x: x["id"] == "TEST_REMOTE_iossifov_2014", data))


def test_datasets_api_unsupported_features_unaccessible(
    admin_client: Client
) -> None:
    response = admin_client.get("/api/v3/datasets/TEST_REMOTE_iossifov_2014")
    assert response
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["phenotype_tool"] is False
    assert data["description_editable"] is False
    assert data["gene_browser"]["enabled"] is False


def test_user_client_get_dataset_details_remote(
        user_client: Client, wdae_gpf_instance: WGPFInstance
) -> None:

    response = user_client.get(
        "/api/v3/datasets/details/TEST_REMOTE_iossifov_2014")

    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data["hasDenovo"]
