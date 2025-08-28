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
    assert response.status_code == status.HTTP_200_OK


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


def test_histograms_beta(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.post("/api/v3/measures/histogram-beta", {
        "datasetId": "t4c8_study_1", "measure": "i1.age",
    })
    assert response.status_code == 200

    result = response.json()
    assert result["measure"] == "i1.age"
    assert result["description"] is None
    assert result["histogram"]["min_value"] == pytest.approx(68, 0.1)
    assert result["histogram"]["max_value"] == pytest.approx(565.91, 0.1)
    assert result["histogram"]["config"] == {
        "number_of_bins": 100,
        "type": "number",
        "view_range": {
            "max": pytest.approx(565.91, 0.1),
            "min": pytest.approx(68, 0.1),
        },
        "x_log_scale": False,
        "x_min_log": None,
        "y_log_scale": False,
    }
    assert result["histogram"]["out_of_range_bins"] == [0, 0]
    assert result["histogram"]["bars"] == [
        2, 0, 3, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 2, 1,
    ]
    assert result["histogram"]["bins"] == [
        pytest.approx(68.00, 0.1),
        pytest.approx(87.91, 0.1),
        pytest.approx(107.83, 0.1),
        pytest.approx(127.75, 0.1),
        pytest.approx(147.66, 0.1),
        pytest.approx(167.58, 0.1),
        pytest.approx(187.49, 0.1),
        pytest.approx(207.41, 0.1),
        pytest.approx(227.33, 0.1),
        pytest.approx(247.24, 0.1),
        pytest.approx(267.16, 0.1),
        pytest.approx(287.08, 0.1),
        pytest.approx(306.99, 0.1),
        pytest.approx(326.91, 0.1),
        pytest.approx(346.83, 0.1),
        pytest.approx(366.74, 0.1),
        pytest.approx(386.66, 0.1),
        pytest.approx(406.57, 0.1),
        pytest.approx(426.49, 0.1),
        pytest.approx(446.41, 0.1),
        pytest.approx(466.32, 0.1),
        pytest.approx(486.24, 0.1),
        pytest.approx(506.16, 0.1),
        pytest.approx(526.07, 0.1),
        pytest.approx(545.99, 0.1),
        pytest.approx(565.91, 0.1),
    ]


def test_role_list(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.post("/api/v3/measures/role-list", {
        "datasetId": "t4c8_study_1",
    })
    assert response.status_code == 200
    assert response.content == b'["dad","mom","prb","sib"]'
