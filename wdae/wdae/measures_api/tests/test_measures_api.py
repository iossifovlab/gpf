import pytest


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


MEASURES_URL = "/api/v3/measures/type"
REGRESSIONS_URL = "/api/v3/measures/regressions"


def test_measures_list_categorical(admin_client):
    response = admin_client.get(
        f"{MEASURES_URL}/categorical?datasetId=quads_f1"
    )

    assert response.status_code == 200
    assert len(response.data) == 1


def test_measures_list_continuous(admin_client):
    response = admin_client.get(
        f"{MEASURES_URL}/continuous?datasetId=quads_f1"
    )

    assert response.status_code == 200
    assert len(response.data) == 1


def test_regressions(admin_client):
    response = admin_client.get(f"{REGRESSIONS_URL}?datasetId=comp")
    assert response.status_code == 200
    assert "age" in response.data
    assert "iq" in response.data
