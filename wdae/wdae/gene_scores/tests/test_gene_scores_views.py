# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_gene_scores_list_view(user_client):
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.data
    print([d["score"] for d in data])
    assert len(data) == 5

    for score in response.data:
        assert "desc" in score
        assert "score" in score
        assert "bars" in score
        assert "bins" in score


def test_gene_scores_get_genes_view(user_client):
    url = "/api/v3/gene_scores/genes"
    data = {
        "score": "LGD_rank",
        "min": 1.5,
        "max": 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 200
    print(response.data)

    assert len(response.data) == 3


def test_gene_scores_partitions(user_client):
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "min": 1.5,
        "max": 5.0
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 200

    data = response.data
    assert len(data) == 3
    assert data["left"]["count"] == 1
    assert data["right"]["count"] == 18454


def test_gene_scores_partitions_bad_request_no_min(user_client):
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "min": 1.5
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 400


def test_gene_scores_partitions_bad_request_no_max(user_client):
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "max": 5.0
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 400


def test_gene_scores_partitions_bad_request_non_float_min(user_client):
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "min": "non-float-value",
        "max": 5.0
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 400


def test_gene_scores_partitions_bad_request_non_float_max(user_client):
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "min": 1.5,
        "max": "non-float-value"
    }

    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 400
