# pylint: disable=W0621,C0114,C0116,W0212,W0613
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance

ROUTE_PREFIX = "/api/v3/gene_profiles"


def test_configuration(
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    admin_client: Client,
) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/configuration")

    assert response.status_code == 200
    assert response.data == {}  # type: ignore
