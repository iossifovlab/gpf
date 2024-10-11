# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any

import pytest
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


@pytest.mark.parametrize("url,method,body,status", [
    (
        "/api/v3/gene_view/config?datasetId=t4c8_study_1",
        "get",
        None,
        status.HTTP_401_UNAUTHORIZED,
    ),
    (
        "/api/v3/gene_view/query_summary_variants",
        "post",
        {"datasetId": "t4c8_study_1"},
        status.HTTP_200_OK,
    ),
    (
        "/api/v3/gene_view/download_summary_variants",
        "post",
        {"datasetId": "t4c8_study_1"},
        status.HTTP_200_OK,
    ),
])
def test_gene_view_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict,
    status: Any,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status


def test_gene_view_summary_variants_query(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {"datasetId": "t4c8_study_1"}
    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.data  # type: ignore
    assert len(res) == 6
    assert len(res[0]["alleles"]) == 2
    assert len(res[1]["alleles"]) == 1
    assert len(res[2]["alleles"]) == 2
    assert len(res[3]["alleles"]) == 2
    assert len(res[4]["alleles"]) == 2
    assert len(res[5]["alleles"]) == 2


def test_gene_view_config(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=t4c8_study_1",
    )
    assert response.status_code == status.HTTP_200_OK
