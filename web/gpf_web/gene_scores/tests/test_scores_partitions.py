# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance


def test_gene_scores_partitions(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
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
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
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
