# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_gene_scores_partitions(user_client: Client) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "LGD_rank",
        "min": 1.5,
        "max": 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200


def test_gene_scores_partitions_rvis(user_client: Client) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "RVIS_rank",
        "min": 1,
        "max": 100,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200


def test_bad_gene_score_partition(user_client: Client) -> None:
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


def test_full_patition(user_client: Client) -> None:
    url = "/api/v3/gene_scores/partitions"
    data = {
        "score": "RVIS_rank",
        "min": 0,
        "max": 1000,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200
