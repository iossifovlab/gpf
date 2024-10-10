# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import os
from typing import Any

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/common_reports/studies/t4c8_study_1", "get", None),
    ("/api/v3/common_reports/studies/t4c8_study_1/full", "get", None),
    (
        "/api/v3/common_reports/family_counters",
        "post",
        {
            "study_id": "t4c8_study_1",
            "group_name": "Phenotype",
            "counter_id": "0",
        }),
    (
        "/api/v3/common_reports/family_counters/download",
        "post",
        {
            "queryData": json.dumps({
                "study_id": "t4c8_study_1",
                "group_name": "Phenotype",
                "counter_id": "0",
            }),
        },
    ),
    ("/api/v3/common_reports/families_data/t4c8_study_1", "get", None),
])
def test_variant_reports_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict[str, Any],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    print(response.headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_variant_reports(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/studies/t4c8_study_1"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data


def test_variant_reports_full(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/studies/t4c8_study_1/full"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data


def test_family_counters(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "study_id": "t4c8_study_1",
        "group_name": "Phenotype",
        "counter_id": "0",
    }
    url = "/api/v3/common_reports/family_counters"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    print(data)
    assert list(data) == ["f1.1"]


def test_family_counters_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "queryData": json.dumps({
            "study_id": "t4c8_study_1",
            "group_name": "Phenotype",
            "counter_id": "0",
        }),
    }
    url = "/api/v3/common_reports/family_counters/download"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)  # type: ignore
    print(b"".join(res).decode())

    assert len(res) == 5


def test_families_tags_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = (
        "/api/v3/common_reports/families_data/t4c8_dataset"
    )
    body = {
        "tagsQuery": {
            "orMode": False,
            "includeTags": ["tag_nuclear_family", "tag_trio_family"],
            "excludeTags": [],
        },
    }
    response = admin_client.post(
        url, json.dumps(body), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)  # type: ignore
    print(b"".join(res).decode())
    assert len(res) == 4


@pytest.mark.parametrize(
    "body",
    [
        {
            "tagsQuery": {
                "orMode": False,
                "includeTags": ["tag_nuclear_family", "tag_trio_family"],
            },
        },
        {
            "tagsQuery": {
                "orMode": False,
                "excludeTags": [],
            },
        },
        {
            "tagsQuery": {
                "includeTags": ["tag_nuclear_family", "tag_trio_family"],
                "excludeTags": [],
            },
        },
        {
            "tagsQuery": {
                "orMode": "test",
                "includeTags": ["tag_nuclear_family", "tag_trio_family"],
                "excludeTags": [],
            },
        },
        {
            "tagsQuery": {
                "orMode": False,
                "includeTags": "asfag",
                "excludeTags": [],
            },
        },
        {
            "tagsQuery": {},
        },
    ],
)
def test_families_tags_download_errors_on_bad_body(
    admin_client: Client, body: dict[str, Any],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = (
        "/api/v3/common_reports/families_data/t4c8_study_1"
    )
    response = admin_client.post(
        url, json.dumps(body), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_variant_reports_no_permissions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/studies/t4c8_study_1"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN

    data = response.data  # type: ignore
    assert data


def test_autogenerate_common_report(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    study = t4c8_wgpf_instance.get_genotype_data("t4c8_study_1")
    assert study is not None
    report_filename = study.config.common_report.file_path
    os.remove(report_filename)
    assert not os.path.exists(report_filename)

    url = "/api/v3/common_reports/studies/t4c8_study_1"
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == "t4c8_study_1"  # type: ignore

    assert os.path.exists(report_filename)


def test_families_data_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/families_data/t4c8_study_1"
    response = admin_client.post(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)  # type: ignore
    assert streaming_content

    assert len(streaming_content) == 9


def test_families_data_download_no_permissions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/families_data/t4c8_study_1"
    response = user_client.post(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_families_data_all_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/families_data/t4c8_study_1"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)  # type: ignore
    assert streaming_content

    assert len(streaming_content) == 9


def test_families_data_all_download_no_permissions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/families_data/t4c8_study_1"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN
