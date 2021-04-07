import pytest

import json

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_gene_weights_partitions(user_client):
    url = "/api/v3/gene_weights/partitions"
    data = {
        "weight": "LGD_rank",
        "min": 1.5,
        "max": 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 200


def test_gene_weights_partitions_rvis(user_client):
    url = "/api/v3/gene_weights/partitions"
    data = {
        "weight": "RVIS_rank",
        "min": 1,
        "max": 100,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 200


def test_bad_gene_weight_partition(user_client):
    url = "/api/v3/gene_weights/partitions"
    data = {
        "weight": "ala-bala",
        "min": -8,
        "max": -3,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 404


def test_full_patition(user_client):
    url = "/api/v3/gene_weights/partitions"
    data = {
        "weight": "RVIS_rank",
        "min": 0,
        "max": 1000,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == 200
