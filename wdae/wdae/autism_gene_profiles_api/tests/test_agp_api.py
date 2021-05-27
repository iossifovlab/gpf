import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance_agp",
    "dae_calc_gene_sets",
    "agp_gpf_instance",
)

route_prefix = "/api/v3/autism_gene_tool"


def test_configuration(admin_client):
    response = admin_client.get(f"{route_prefix}/configuration")

    assert response.status_code == 200
    print(response.data)

    assert len(response.data["genomicScores"]) == 2

    assert len(response.data["genomicScores"][0]["scores"]) == 3
    assert response.data["genomicScores"][0]["category"] == \
        "protection_scores"

    assert len(response.data["genomicScores"][1]["scores"]) == 3
    assert response.data["genomicScores"][1]["category"] == "autism_scores"

    datasets = response.data["datasets"]
    assert len(datasets) == 1
    assert datasets[0]["id"] == "iossifov_we2014_test"
    assert len(datasets[0]["statistics"]) == 2
    assert len(datasets[0]["personSets"]) == 2
    assert datasets[0]["personSets"] == [
        {"setName": "unknown", "collectionName": "phenotype"},
        {"setName": "unaffected", "collectionName": "phenotype"}
    ]


def test_get_statistics(admin_client):
    response = admin_client.get(f"{route_prefix}/genes")
    assert response.status_code == 200
    print(response.data)


def test_get_statistic(admin_client):
    response = admin_client.get(f"{route_prefix}/genes/CHD8")
    assert response.status_code == 200
    print(response.data)
