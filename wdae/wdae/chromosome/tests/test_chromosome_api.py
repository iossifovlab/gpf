import pytest

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


def test_chromosome_api_get(user_client):
    response = user_client.get("/api/v3/chromosomes")

    assert response
    assert response.status_code == 200

    data = response.data

    assert len(response.data) == 3
    assert data[0]["name"] == "1"
    assert data[1]["name"] == "2"
    assert data[2]["name"] == "3"
    assert len(data[0]["bands"]) == 7
    assert data[0]["bands"][0]["start"] == 0
    assert data[0]["bands"][0]["end"] == 2300000
    assert data[0]["bands"][0]["name"] == "p36.33"
    assert data[0]["bands"][0]["gieStain"] == "gneg"
    assert data[0]["bands"][5]["start"] == 12700000
    assert data[0]["bands"][5]["end"] == 16200000
    assert data[0]["bands"][5]["name"] == "p36.21"
    assert data[0]["bands"][5]["gieStain"] == "gpos50"
    assert data[1]["bands"][3]["name"] == "p24.3"
    assert data[1]["bands"][6]["name"] == "p23.3"
    assert data[1]["bands"][9]["name"] == "p22.3"
    assert data[2]["bands"][0]["name"] == "p25.3"
    assert data[2]["bands"][3]["name"] == "p24.3"
