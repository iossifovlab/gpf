# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


def test_get_genomic_scores(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)

    data = response.data  # type: ignore
    assert sorted([gs["score"] for gs in data]) == ["score_one"]
