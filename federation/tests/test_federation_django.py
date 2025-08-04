# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from collections.abc import Iterator
from typing import cast

import pytest
from django.http import StreamingHttpResponse
from django.test.client import Client
from federation.remote_study_wrapper import RemoteWDAEStudy
from gpf_instance.gpf_instance import WGPFInstance
from pheno_browser_api.tests.test_pheno_browser_api import DOWNLOAD_URL
from rest_framework import status
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


def test_studies(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_ids = {
        "t4c8_dataset", "t4c8_study_1", "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1", "t4c8_study_2", "TEST_REMOTE_t4c8_study_4",
        "study_1_pheno", "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno", "t4c8_study_4",
    }

    response = admin_client.get("/api/v3/datasets")
    assert response is not None
    assert response.status_code == 200

    dataset_ids = {item["id"] for item in response.json()["data"]}
    assert dataset_ids == expected_ids


def test_genomic_scores(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_scores = {"score_one", "TEST_REMOTE_score_one"}

    response = admin_client.get("/api/v3/genomic_scores")
    assert response
    assert response.status_code == 200

    returned_scores = {item["score"] for item in response.json()}
    assert returned_scores == expected_scores


def test_gene_sets(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_names = {"main", "denovo", "TEST_REMOTE_main"}

    response = admin_client.get("/api/v3/gene_sets/gene_sets_collections")
    assert response
    assert response.status_code == 200

    returned_names = {item["name"] for item in response.json()}
    assert returned_names == expected_names


def test_measures_regressions(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_measures = {"age", "iq"}

    response = admin_client.get(
        "/api/v3/measures/regressions?datasetId=TEST_REMOTE_study_1_pheno")
    assert response
    assert response.status_code == 200

    returned_measures = set(response.json().keys())
    assert returned_measures == expected_measures


def test_pheno_tool(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "measureId": "i1.m1",
        "normalizeBy": [],
        "effectTypes": ["missense", "frame-shift", "synonymous"],
        "presentInParent": {"presentInParent": ["neither"]},
    }

    response = admin_client.post(
        "/api/v3/pheno_tool",
        data=json.dumps(query),
        content_type="application/json",
    )
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 3

    results_by_effect = {r["effect"]: r for r in results}

    missense = results_by_effect["missense"]
    assert missense["femaleResults"]["positive"]["count"] == 1
    assert missense["femaleResults"]["positive"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert missense["femaleResults"]["negative"]["count"] == 1
    assert missense["femaleResults"]["negative"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)
    assert missense["maleResults"]["positive"]["count"] == 0
    assert missense["maleResults"]["negative"]["count"] == 0

    frameshift = results_by_effect["frame-shift"]
    assert frameshift["femaleResults"]["negative"]["count"] == 2
    assert frameshift["femaleResults"]["negative"]["mean"] == \
        pytest.approx(103.67282485961914, abs=1e-3)
    assert frameshift["femaleResults"]["positive"]["count"] == 0
    assert frameshift["femaleResults"]["positive"]["mean"] == \
        pytest.approx(103.67282485961914, abs=1e-3)
    assert frameshift["maleResults"]["positive"]["count"] == 0
    assert frameshift["maleResults"]["negative"]["count"] == 0

    synonymous = results_by_effect["synonymous"]
    assert synonymous["femaleResults"]["positive"]["count"] == 1
    assert synonymous["femaleResults"]["positive"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)
    assert synonymous["femaleResults"]["negative"]["count"] == 1
    assert synonymous["femaleResults"]["negative"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert synonymous["maleResults"]["positive"]["count"] == 0
    assert synonymous["maleResults"]["negative"]["count"] == 0


def test_enrichment_models(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = admin_client.get(
        "/api/v3/enrichment/models/TEST_REMOTE_t4c8_dataset")
    assert response
    assert response.status_code == 200
    result = response.json()

    assert result["background"][0]["id"] == "coding_len_background"
    assert result["counting"][0]["id"] == "enrichment_gene_counting"
    assert result["counting"][1]["id"] == "enrichment_events_counting"
    assert result["defaultBackground"] == "coding_len_background"
    assert result["defaultCounting"] == "enrichment_gene_counting"


def test_enrichment_test(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_dataset",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSet": {
            "geneSetsCollection": "main",
            "geneSet": "t4_candidates",
        },
    }
    response = admin_client.post(
        "/api/v3/enrichment/test",
        data=json.dumps(query),
        content_type="application/json",
    )

    assert response
    assert response.status_code == 200

    result_remote = response.data  # type: ignore
    assert set(result_remote.keys()) == {"desc", "result"}
    assert result_remote["desc"] == "Gene Set: T4 Candidates (1)"
    assert len(result_remote["result"]) == 4

    query["datasetId"] = "t4c8_dataset"
    response = admin_client.post(
        "/api/v3/enrichment/test",
        data=json.dumps(query),
        content_type="application/json",
    )
    result_local = response.data  # type: ignore
    assert result_local == result_remote


def test_gene_view_config(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=TEST_REMOTE_t4c8_study_1",
    )
    assert response.status_code == status.HTTP_200_OK


def test_gene_view_summary_variants_query(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {"datasetId": "TEST_REMOTE_t4c8_study_1", "geneSymbols": ["t4"]}
    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    res = response.data  # type: ignore
    assert len(res) == 1
    assert len(res[0]["alleles"]) == 1


def test_gene_view_summary_variants_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "queryData": json.dumps({
            "datasetId": "TEST_REMOTE_t4c8_study_1",
            "geneSymbols": ["t4"],
            "download": True,
        }),
    }

    response = admin_client.post(
        "/api/v3/gene_view/download_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    lines = list(response.streaming_content)  # type: ignore
    assert len(lines) == 3


def test_query_variants_wdae_remote(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_study_1")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    result = list(remote_study.query_variants_wdae(
        {}, [], t4c8_query_transformer, t4c8_response_transformer))
    assert len(result) == 12


def test_query_variants_wdae_remote_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "download": True,
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = "".join([
        p.decode("utf8")
        for p in response.streaming_content
    ]).split("\n")
    res = [r for r in res if r]
    assert len(res) == 13


def test_genotype_browser_query_default_person_set_collection(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {"datasetId": "TEST_REMOTE_t4c8_study_1"}
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        p.decode("utf8") for p in response.streaming_content if p).split("\n")
    res = [r for r in res if r]

    first_row = json.loads(res[0])
    assert any(
        cell[6] != "#ffffff"
        for row in first_row
        for cell in row[4]
    )


def test_genotype_browser_query_explicit_person_set_collection(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "personSetCollection": {
            "id": "phenotype",
            "checkedValues": ["autism"],
        },
    }

    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        p.decode("utf8") for p in response.streaming_content if p).split("\n")
    res = [r for r in res if r]

    first_row = json.loads(res[0])
    assert any(
        cell[6] != "#ffffff"
        for row in first_row
        for cell in row[4]
    )


def test_pheno_browser_instruments(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    instruments_url = "/api/v3/pheno_browser/instruments"
    response_remote = admin_client.get(
        instruments_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
        },
    )

    assert response_remote.status_code == 200

    response_local = admin_client.get(
        instruments_url,
        {
            "dataset_id": "t4c8_study_1",
        },
    )

    assert response_local.status_code == 200

    assert response_remote.json() == response_local.json()


def test_pheno_browser_measures_info(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    info_url = "/api/v3/pheno_browser/measures_info"
    response_remote = admin_client.get(
        info_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
        },
    )

    assert response_remote.status_code == 200

    response_local = admin_client.get(
        info_url,
        {
            "dataset_id": "t4c8_study_1",
        },
    )

    assert response_local.status_code == 200

    assert response_remote.json() == response_local.json()


def test_pheno_browser_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    download_url = "/api/v3/pheno_browser/download"
    response_remote = cast(StreamingHttpResponse, admin_client.get(
        download_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "instrument": "i1",
        },
    ))

    assert response_remote.status_code == 200

    response_local = cast(StreamingHttpResponse, admin_client.get(
        download_url,
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
        },
    ))

    assert response_local.status_code == 200

    local_first_line = next(
        cast(Iterator[bytes], response_local.streaming_content))
    remote_first_line = next(
        cast(Iterator[bytes], response_local.streaming_content))

    assert remote_first_line.decode("utf-8") == local_first_line.decode("utf-8")
