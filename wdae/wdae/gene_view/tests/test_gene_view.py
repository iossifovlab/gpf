# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import operator
from typing import Any
from unittest.mock import patch

import pytest
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from dae.utils.regions import Region


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
        "/api/v3/gene_view/query_summary_variants",
        "post",
        {"datasetId": "t4c8_dataset"},
        status.HTTP_200_OK,
    ),
    (
        "/api/v3/gene_view/download_summary_variants",
        "post",
        {"queryData": json.dumps({"datasetId": "t4c8_study_2"})},
        status.HTTP_200_OK,
    ),
    (
        "/api/v3/gene_view/download_summary_variants",
        "post",
        {"queryData": json.dumps({"datasetId": "t4c8_dataset"})},
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


def test_gene_view_summary_variants_query_group(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {"datasetId": "t4c8_dataset"}
    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = sorted(response.json(), key=operator.itemgetter("svuid"))

    assert len(res) == 9
    assert len(res[0]["alleles"]) == 2
    assert len(res[1]["alleles"]) == 2
    assert len(res[2]["alleles"]) == 2
    assert len(res[3]["alleles"]) == 2
    assert len(res[4]["alleles"]) == 1
    assert len(res[5]["alleles"]) == 1
    assert len(res[6]["alleles"]) == 1
    assert len(res[7]["alleles"]) == 1
    assert len(res[8]["alleles"]) == 2


def test_gene_view_summary_variants_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {"queryData": json.dumps({"datasetId": "t4c8_study_1"})}
    response = admin_client.post(
        "/api/v3/gene_view/download_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    lines = list(response.streaming_content)  # type: ignore
    assert len(lines) == 13


def test_gene_view_summary_variants_download_group(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {"queryData": json.dumps({"datasetId": "t4c8_dataset"})}
    response = admin_client.post(
        "/api/v3/gene_view/download_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    lines = list(response.streaming_content)  # type: ignore
    assert len(lines) == 16


def test_gene_view_config(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=t4c8_study_1",
    )
    assert response.status_code == status.HTTP_200_OK


summary_query_kwargs_expected = [
    (
        {"regions": ["chr1:1-100"]},
        {"regions": [Region("chr1", 1, 100)]},

    ),
    (
        {"genes": ["t4"]},
        {"genes": ["t4"]},
    ),
    (
        {
            "effectTypes": [
                "frame-shift", "nonsense", "splice-site",
                "no-frame-shift-newStop", "missense", "no-frame-shift",
                "noStart", "noEnd", "synonymous", "CNV+", "CNV-", "CDS",
            ],
        },
        {
            "effect_types": [
                "frame-shift", "nonsense", "splice-site",
                "no-frame-shift-newStop", "missense", "no-frame-shift",
                "noStart", "noEnd", "synonymous", "CNV+", "CNV-", "CDS",
            ],
        },
    ),
    (
        {"variantTypes": ["sub"]},
        {"variant_type": "substitution"},
    ),
    (
        {"studyFilters": ["t4c8_dataset", "t4c8_study_1"]},
        {"study_filters": {"t4c8_dataset", "t4c8_study_1"}},
    ),
    (
        {"limit": 10000},
        {"limit": 10000},
    ),
    (
        {"return_unknown": True},
        {"return_unknown": True},
    ),
    (
        {"return_reference": True},
        {"return_reference": True},
    ),
    (
        {"frequency_filter": True},
        {"frequency_filter": True},
    ),
    (
        {"category_attr_filter": [{"test": "test"}]},
        {"category_attr_filter": [{"test": "test"}]},
    ),
    (
        {"real_attr_filter": [{"test": "test"}]},
        {"real_attr_filter": [{"test": "test"}]},
    ),
    (
        {"ultra_rare": True},
        {"ultra_rare": True},
    ),
]


@pytest.mark.parametrize("data,expected", summary_query_kwargs_expected)
def test_query_gene_view_summary_variants_dataset(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    data: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    data["geneSymbols"] = ["t4"]
    with patch(
        "dae.studies.study.GenotypeDataStudy.create_summary_query_runners",
    ) as mock_create:
        mock_create.return_value = []
        response = admin_client.post(
            "/api/v3/gene_view/query_summary_variants",
            json.dumps(
                dict(data, datasetId="t4c8_dataset", geneSymbols=["t4"]),
            ),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        mock_create.assert_called()

        called_kwargs = mock_create.call_args.kwargs
        for key, value in expected.items():
            assert called_kwargs[key] == value


@pytest.mark.parametrize("data,expected", summary_query_kwargs_expected)
def test_query_gene_view_summary_variants_download_dataset(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    data: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    data["geneSymbols"] = ["t4"]
    with patch(
        "dae.studies.study.GenotypeDataStudy.create_summary_query_runners",
    ) as mock_create:
        mock_create.return_value = []
        query_data = {
            "queryData": json.dumps({
                **data,
                "geneSymbols": ["t4"],
                "datasetId": "t4c8_study_1",
                "download": True,
            }),
        }
        response = admin_client.post(
            "/api/v3/gene_view/download_summary_variants",
            json.dumps(query_data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        _ = list(response.streaming_content)  # type: ignore
        mock_create.assert_called()

        called_kwargs = mock_create.call_args.kwargs
        for key, value in expected.items():
            assert called_kwargs[key] == value


@pytest.mark.parametrize("data,expected", summary_query_kwargs_expected)
def test_query_gene_view_summary_variants_study(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    data: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    data["geneSymbols"] = ["t4"]
    with patch(
        "dae.studies.study.GenotypeDataStudy.create_summary_query_runners",
    ) as mock_create:
        mock_create.return_value = []
        response = admin_client.post(
            "/api/v3/gene_view/query_summary_variants",
            json.dumps(
                dict(data, datasetId="t4c8_study_1", geneSymbols=["t4"]),
            ),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        mock_create.assert_called()

        called_kwargs = mock_create.call_args.kwargs
        for key, value in expected.items():
            assert called_kwargs[key] == value


@pytest.mark.parametrize("data,expected", summary_query_kwargs_expected)
def test_query_gene_view_summary_variants_download_study(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    data: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    data["geneSymbols"] = ["t4"]
    with patch(
        "dae.studies.study.GenotypeDataStudy.create_summary_query_runners",
    ) as mock_create:
        mock_create.return_value = []
        query_data = {
            "queryData": json.dumps({
                **data,
                "geneSymbols": ["t4"],
                "datasetId": "t4c8_dataset",
                "download": True,
            }),
        }
        response = admin_client.post(
            "/api/v3/gene_view/download_summary_variants",
            json.dumps(query_data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        _ = list(response.streaming_content)  # type: ignore
        mock_create.assert_called()

        called_kwargs = mock_create.call_args.kwargs
        for key, value in expected.items():
            assert called_kwargs[key] == value
