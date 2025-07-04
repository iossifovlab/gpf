# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance


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
        "/api/v3/measures/regressions?datasetId=study_1_pheno")
    assert response
    assert response.status_code == 200

    returned_measures = set(response.json().keys())
    assert returned_measures == expected_measures


def test_measures_continuous(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_measures = {"i1.age", "i1.iq", "i1.m1", "i1.m2", "i1.m3"}

    response = admin_client.get(
        "/api/v3/measures/type/continuous?datasetId=study_1_pheno")
    assert response
    assert response.status_code == 200

    returned_measures = {item["measure"] for item in response.json()}
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
