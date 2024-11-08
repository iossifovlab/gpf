# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import operator

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/enrichment/models/t4c8_study_1", "GET", None),
    ("/api/v3/enrichment/test", "POST",
     {
         "datasetId": "t4c8_study_1",
         "enrichmentBackgroundModel": "coding_len_background",
         "enrichmentCountingModel": "enrichment_gene_counting",
         "geneSymbols": ["T4", "C8"],
     }),
])
def test_enrichment_api_permissions(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
    url: str,
    method: str,
    body: dict[str, str | list[str]] | None,
) -> None:
    if method == "GET":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_200_OK


def test_enrichment_models(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/enrichment/models/t4c8_study_1")

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore
    assert result

    assert len(result["background"]) == 1
    background = result["background"]
    assert background[0]["id"] == "coding_len_background"
    assert background[0]["name"] == "t4c8CodingLenBackground"
    assert background[0]["desc"] == "T4C8 gene coding length enrichment background model"  # noqa: E501

    assert len(result["counting"]) == 2
    counting = result["counting"]
    counting.sort(key=operator.itemgetter("name"))

    assert counting[0]["id"] == "enrichment_gene_counting"
    assert counting[0]["name"] == "Counting affected genes"
    assert counting[0]["desc"] == "Counting affected genes"

    assert counting[1]["id"] == "enrichment_events_counting"
    assert counting[1]["name"] == "Counting events"
    assert counting[1]["desc"] == "Counting events"


def test_enrichment_models_missing_study(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/enrichment/models/f1")
    assert response
    assert response.status_code == 404


def test_enrichment_test_missing_dataset_id(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["T4"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 400


def test_enrichment_test_missing_study(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_9001",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["T4"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 404


def test_enrichment_test_missing_gene_symbols(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_1",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 400


def test_enrichment_test_with_gene_symbols(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_1",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["T4", "C8"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore

    assert set(result.keys()) == {"desc", "result"}
    assert result["desc"] == "Gene Symbols: C8,T4 (2)"
    assert len(result["result"]) == 2
    assert len(result["result"][0]) == 18
    assert len(result["result"][1]) == 18


def test_enrichment_test_with_gene_score(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_1",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneScores": {
            "score": "t4c8_score",
            "rangeStart": 15,
            "rangeEnd": 20,
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore

    assert set(result.keys()) == {"desc", "result"}
    assert result["desc"] == "Gene Scores: t4c8_score from 15 up to 20 (1)"


def test_enrichment_test_with_gene_score_with_zero_range(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_1",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneScores": {
            "score": "t4c8_score",
            "rangeStart": 0,
            "rangeEnd": 20,
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore

    assert set(result.keys()) == {"desc", "result"}
    assert result["desc"] == "Gene Scores: t4c8_score from 0 up to 20 (2)"


def test_enrichment_test_with_gene_set(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "t4c8_study_1",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSet": {
            "geneSetsCollection": "main",
            "geneSet": "t4_candidates",
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore

    assert set(result.keys()) == {"desc", "result"}
    assert result["desc"] == "Gene Set: T4 Candidates (1)"
