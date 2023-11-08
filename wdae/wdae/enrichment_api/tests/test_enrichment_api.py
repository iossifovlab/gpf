# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Dict, List, Optional, Union

import pytest

from rest_framework import status
from django.test.client import Client

from gpf_instance.gpf_instance import WGPFInstance


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/enrichment/models/f1_trio", "get", None),
    (
        "/api/v3/enrichment/test",
        "post",
        {
            "datasetId": "f1_trio",
            "enrichmentBackgroundModel": "coding_len_background_model",
            "enrichmentCountingModel": "enrichment_gene_counting",
            "geneSymbols": ["SAMD11", "PLEKHN1", "POGZ"],
        }
    ),
])
def test_enrichment_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: Optional[Dict[str, Union[str, List[str]]]]
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_enrichment_models(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/enrichment/models/f1_trio")

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore
    assert result

    assert len(result["background"]) == 2
    background = result["background"]
    background.sort(key=lambda x: x["id"])
    assert background[0]["id"] == "enrichment/coding_len_testing"
    assert background[0]["name"] == "CodingLenBackground"
    assert background[0]["description"] == ""

    assert background[1]["id"] == "enrichment/samocha_testing"
    assert background[1]["name"] == "Samocha's enrichment background model"
    assert background[1]["description"] == ""

    assert len(result["counting"]) == 2

    counting = result["counting"]
    counting.sort(key=lambda x: x["name"])

    assert counting[0]["id"] == "enrichment_events_counting"
    assert counting[0]["name"] == "enrichment_events_counting"
    assert counting[0]["desc"] == "Enrichment Events Counting"

    assert counting[1]["id"] == "enrichment_gene_counting"
    assert counting[1]["name"] == "enrichment_gene_counting"
    assert counting[1]["desc"] == "Enrichment Gene Counting"


def test_enrichment_models_missing_study(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/enrichment/models/f1")

    assert response
    assert response.status_code == 404


def test_enrichment_test_missing_dataset_id(admin_client: Client) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "enrichmentBackgroundModel": "enrichment/coding_len_testing",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["POGZ"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 400


def test_enrichment_test_missing_study(admin_client: Client) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1",
        "enrichmentBackgroundModel": "enrichment/coding_len_testing",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["POGZ"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 404


def test_enrichment_test_missing_gene_symbols(admin_client: Client) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1_trio",
        "enrichmentBackgroundModel": "enrichment/coding_len_testing",
        "enrichmentCountingModel": "enrichment_gene_counting",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 400


# @pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_enrichment_test_gene_symbols(admin_client: Client) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1_trio",
        "enrichmentBackgroundModel": "enrichment/coding_len_testing",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSymbols": ["SAMD11", "PLEKHN1", "POGZ"],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore
    assert len(result) == 2

    assert result["desc"][:14] == "Gene Symbols: "
    assert result["desc"][:14] == "Gene Symbols: "
    assert result["desc"][-4:] == " (3)"
    assert sorted(result["desc"][14:-4].split(",")) == sorted(
        ["SAMD11", "PLEKHN1", "POGZ"]
    )

    assert len(result["result"]) == 2
    assert len(result["result"][0]) == 6
    assert result["result"][0]["selector"] == "phenotype 1"
    assert result["result"][0]["peopleGroupId"] == "phenotype"
    assert len(result["result"][0]["childrenStats"]) == 3
    assert result["result"][0]["childrenStats"]["M"] == 1
    assert result["result"][0]["childrenStats"]["F"] == 1
    assert result["result"][0]["childrenStats"]["U"] == 0
    assert result["result"][0]["LGDs"]["all"]["count"] == 0
    assert result["result"][0]["LGDs"]["rec"]["count"] == 0
    assert result["result"][0]["LGDs"]["male"]["count"] == 0
    assert result["result"][0]["LGDs"]["female"]["count"] == 0
    assert result["result"][0]["missense"]["all"]["count"] == 1
    assert result["result"][0]["missense"]["rec"]["count"] == 1
    assert result["result"][0]["missense"]["male"]["count"] == 1
    assert result["result"][0]["missense"]["female"]["count"] == 1
    assert result["result"][0]["synonymous"]["all"]["count"] == 1
    assert result["result"][0]["synonymous"]["rec"]["count"] == 1
    assert result["result"][0]["synonymous"]["male"]["count"] == 1
    assert result["result"][0]["synonymous"]["female"]["count"] == 1

    assert len(result["result"][1]) == 6
    assert result["result"][1]["selector"] == "unaffected"
    assert result["result"][1]["peopleGroupId"] == "phenotype"
    assert len(result["result"][1]["childrenStats"]) == 3
    assert result["result"][1]["childrenStats"]["F"] == 1
    assert result["result"][1]["childrenStats"]["M"] == 0
    assert result["result"][1]["childrenStats"]["U"] == 0
    assert result["result"][1]["LGDs"]["all"]["count"] == 0
    assert result["result"][1]["LGDs"]["rec"]["count"] == 0
    assert result["result"][1]["LGDs"]["male"]["count"] == 0
    assert result["result"][1]["LGDs"]["female"]["count"] == 0
    assert result["result"][1]["missense"]["all"]["count"] == 0
    assert result["result"][1]["missense"]["rec"]["count"] == 0
    assert result["result"][1]["missense"]["male"]["count"] == 0
    assert result["result"][1]["missense"]["female"]["count"] == 0
    assert result["result"][1]["synonymous"]["all"]["count"] == 1
    assert result["result"][1]["synonymous"]["rec"]["count"] == 0
    assert result["result"][1]["synonymous"]["male"]["count"] == 0
    assert result["result"][1]["synonymous"]["female"]["count"] == 1


def test_enrichment_test_gene_scores(
    admin_client: Client,
    wdae_gpf_instance: WGPFInstance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1_trio",
        "enrichmentBackgroundModel": "coding_len_background_model",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneScores": {
            "score": "LGD_rank",
            "rangeStart": 1,
            "rangeEnd": 1000
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 200


def test_enrichment_test_gene_scores_with_zero_range(
        admin_client: Client, wdae_gpf_instance: WGPFInstance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1_trio",
        "enrichmentBackgroundModel": "coding_len_background_model",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneScores": {
            "score": "LGD_rank",
            "rangeStart": 0,
            "rangeEnd": 1000
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore
    assert result["desc"] == "Gene Scores: LGD_rank from 0 up to 1000 (1024)"


def test_enrichment_test_gene_set(
    admin_client: Client,
    wdae_gpf_instance: WGPFInstance
) -> None:
    url = "/api/v3/enrichment/test"
    query = {
        "datasetId": "f1_trio",
        "enrichmentBackgroundModel": "coding_len_background_model",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSet": {
            "geneSetsCollection": "denovo",
            "geneSet": "Missense",
            "geneSetsTypes": {"f1_trio": {"phenotype": ["phenotype1"]}},
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert response
    assert response.status_code == 200

    result = response.data  # type: ignore
    assert len(result) == 2

    assert result["desc"] == \
        "Gene Set: Missense (f1_trio:phenotype:phenotype1) (1)"
