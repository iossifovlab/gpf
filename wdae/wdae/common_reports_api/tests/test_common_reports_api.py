# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import json
from typing import Any

import pytest

from rest_framework import status
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets", "use_common_reports"
)


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/common_reports/studies/study4", "get", None),
    ("/api/v3/common_reports/studies/study4/full", "get", None),
    (
        "/api/v3/common_reports/family_counters",
        "post",
        {
            "study_id": "study4",
            "group_name": "Phenotype",
            "counter_id": "0"
        }),
    (
        "/api/v3/common_reports/family_counters/download",
        "post",
        {
            "queryData": json.dumps({
                "study_id": "study4",
                "group_name": "Phenotype",
                "counter_id": "0"
            })
        }
    ),
    ("/api/v3/common_reports/families_data/Study1", "get", None),
])
def test_variant_reports_permissions(
    anonymous_client: Client, url: str,
    method: str, body: dict[str, Any]
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    print(response.headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_variant_reports(admin_client: Client) -> None:
    url = "/api/v3/common_reports/studies/study4"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data


def test_variant_reports_full(admin_client: Client) -> None:
    url = "/api/v3/common_reports/studies/study4/full"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data


def test_family_counters(admin_client: Client) -> None:
    data = {
        "study_id": "study4",
        "group_name": "Phenotype",
        "counter_id": "0"
    }
    url = "/api/v3/common_reports/family_counters"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    print(data)
    assert list(data) == ["f2", "f4"]


def test_family_counters_download(admin_client: Client) -> None:
    data = {
        "queryData": json.dumps({
            "study_id": "study4",
            "group_name": "Phenotype",
            "counter_id": "0"
        })
    }
    url = "/api/v3/common_reports/family_counters/download"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)  # type: ignore
    print(b"".join(res).decode())

    assert len(res) == 14


def test_families_tags_download(admin_client: Client) -> None:
    url = (
        "/api/v3/common_reports/families_data/Study1?"
        "tags=tag_nuclear_family,tag_trio_family"
    )
    response = admin_client.get(
        url, content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)  # type: ignore
    print(b"".join(res).decode())
    assert len(res) == 25


def test_families_tags_download_succeeds_on_empty_tags(
        admin_client: Client) -> None:
    url = "/api/v3/common_reports/families_data/Study1?tags="

    response = admin_client.get(
        url, content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK


def test_variant_reports_no_permissions(user_client: Client) -> None:
    url = "/api/v3/common_reports/studies/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN

    data = response.data  # type: ignore
    assert data


def test_autogenerate_common_report(
    admin_client: Client, wdae_gpf_instance: WGPFInstance
) -> None:
    study = wdae_gpf_instance.get_genotype_data("Study3")
    assert study is not None
    report_filename = study.config.common_report.file_path
    assert not os.path.exists(report_filename)

    url = "/api/v3/common_reports/studies/Study3"
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == "Study3"  # type: ignore

    assert os.path.exists(report_filename)


def test_families_data_download(admin_client: Client) -> None:
    url = "/api/v3/common_reports/families_data/Study1"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)  # type: ignore
    assert streaming_content

    assert len(streaming_content) == 35


def test_families_data_download_no_permissions(user_client: Client) -> None:
    url = "/api/v3/common_reports/families_data/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN
