# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status  # type: ignore

MEASURES_URL = "/api/v3/measures/type"
REGRESSIONS_URL = "/api/v3/measures/regressions"


@pytest.mark.parametrize("url", [
    (f"{MEASURES_URL}/continuous?datasetId=t4c8_study_1"),
    (f"{REGRESSIONS_URL}?datasetId=t4c8_study_1"),
])
def test_measures_api_permissions(
    anonymous_client: Client,
    url: str,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get(url)
    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_measures_list_categorical(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        f"{MEASURES_URL}/categorical?datasetId=t4c8_study_1",
    )

    assert response.status_code == 200
    assert len(response.data) == 2  # type: ignore


def test_measures_list_continuous(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        f"{MEASURES_URL}/continuous?datasetId=t4c8_study_1",
    )

    assert response.status_code == 200
    assert len(response.data) == 5  # type: ignore


def test_regressions(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(f"{REGRESSIONS_URL}?datasetId=t4c8_study_1")
    assert response.status_code == 200
    assert "age" in response.data  # type: ignore
    assert "iq" in response.data  # type: ignore


def test_measures_list_wrong_request(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.post("/api/v3/measures/histogram", {
        "datasetId": "t4c8_study_1", "measure": "i1.age",
    })
    assert response.status_code == 200

    response = admin_client.post("/api/v3/measures/histogram", {
        "datasetId": "t4c8_study_1", "measure": "asian",
    })
    assert response.status_code == 400
