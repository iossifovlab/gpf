import pytest

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance_agp", "calc_gene_sets")

route_prefix = "/api/v3/autism_gene_tool"


def test_configuration(admin_client):
    response = admin_client.get(f"{route_prefix}/configuration")

    assert response.status_code == 200
    print(response.data)
    assert len(response.data["autism_scores"]) == 3
    assert len(response.data["protection_scores"]) == 3
    assert len(response.data["datasets"].keys()) == 1

    datasets = response.data["datasets"]
    assert len(datasets["iossifov_we2014_test"]["effects"]) == 2
    assert len(datasets["iossifov_we2014_test"]["person_sets"]) == 2
    assert datasets["iossifov_we2014_test"]["person_sets"] == [
        "unknown", "unaffected"
    ]


def test_get_statistics(admin_client):
    response = admin_client.get(f"{route_prefix}/genes")
    assert response.status_code == 200
    print(response.data)


def test_get_statistic(admin_client):
    response = admin_client.get(f"{route_prefix}/genes/CHD8")
    assert response.status_code == 200
    print(response.data)
