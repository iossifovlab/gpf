import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance",
    "dae_calc_gene_sets",
    # "agp_gpf_instance",
)

ROUTE_PREFIX = "/api/v3/gene_profiles"


def test_configuration(admin_client):
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/configuration")

    assert response.status_code == 200
    print(response.data)
    assert response.data == dict()
