import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")

route_prefix = "/api/v3/autism_gene_tool"


def test_configuration(admin_client):
    response = admin_client.get(f"{route_prefix}/configuration")

    assert response.status_code == 200
    print(response.data)
    assert response.data == dict()
