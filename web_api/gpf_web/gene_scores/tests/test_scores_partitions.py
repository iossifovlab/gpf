# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client
from gain.gene_scores.gene_scores import GeneScore
from gain.genomic_resources.repository_ids import GR_CONF_FILE_NAME
from gain.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)
from gpf_instance.gpf_instance import WGPFInstance


def test_gene_scores_partitions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "t4c8_score",
        "min": 1.5,
        "max": 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200


def test_bad_gene_score_partition(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "ala-bala",
        "min": -8,
        "max": -3,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 404


def _t4c8_gene_score(data: str) -> GeneScore:
    return GeneScore(build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_score
            filename: data.mem
            separator: "\t"
            scores:
            - id: t4c8_score
              histogram:
                type: number
                number_of_bins: 3
        """,
        "data.mem": convert_to_tab_separated(data),
    }))


def test_gene_scores_partitions_counts_at_the_boundaries(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource_id = t4c8_wgpf_instance.get_gene_score_desc(
        "t4c8_score").resource_id
    gene_score = _t4c8_gene_score("""
            gene   t4c8_score
            A      1.0
            B      1.5
            C      5.0
            D      7.0
        """)
    monkeypatch.setitem(
        t4c8_wgpf_instance.gene_scores_db.gene_scores,
        resource_id, gene_score)
    data = {"score": "t4c8_score", "min": 1.5, "max": 5.0}

    response = user_client.post(
        "/api/v3/gene_scores/partitions",
        json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "left": {"count": 1, "percent": 0.25},
        "mid": {"count": 2, "percent": 0.5},
        "right": {"count": 1, "percent": 0.25},
    }


def test_gene_scores_partitions_count_a_duplicate_gene_once(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource_id = t4c8_wgpf_instance.get_gene_score_desc(
        "t4c8_score").resource_id
    gene_score = _t4c8_gene_score("""
            gene   t4c8_score
            A      1.0
            A      1.0
            B      3.0
            C      7.0
        """)
    monkeypatch.setitem(
        t4c8_wgpf_instance.gene_scores_db.gene_scores,
        resource_id, gene_score)
    data = {"score": "t4c8_score", "min": 1.5, "max": 5.0}

    response = user_client.post(
        "/api/v3/gene_scores/partitions",
        json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "left": {"count": 1, "percent": 1 / 3},
        "mid": {"count": 1, "percent": 1 / 3},
        "right": {"count": 1, "percent": 1 / 3},
    }


def test_gene_scores_partitions_count_a_gene_with_an_in_range_row_first(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource_id = t4c8_wgpf_instance.get_gene_score_desc(
        "t4c8_score").resource_id
    gene_score = _t4c8_gene_score("""
            gene   t4c8_score
            A      3.0
            A      1.0
            B      7.0
        """)
    monkeypatch.setitem(
        t4c8_wgpf_instance.gene_scores_db.gene_scores,
        resource_id, gene_score)
    data = {"score": "t4c8_score", "min": 1.5, "max": 5.0}

    response = user_client.post(
        "/api/v3/gene_scores/partitions",
        json.dumps(data), content_type="application/json", format="json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "left": {"count": 1, "percent": 0.5},
        "mid": {"count": 1, "percent": 0.5},
        "right": {"count": 1, "percent": 0.5},
    }
    assert response.json()["mid"]["count"] == len(gene_score.get_genes(
        "t4c8_score", score_min=1.5, score_max=5.0))
