import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_datasets_api_get_remote_studies(admin_client, remote_settings):
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200

    data = response.json()["data"]

    assert any(map(lambda x: x["id"] == "TEST_REMOTE_iossifov_2014", data))
