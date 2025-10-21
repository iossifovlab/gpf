# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance


def test_gene_scores_list_view(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    print([d["score"] for d in data])
    assert len(data) == 1

    for score in data:
        assert "desc" in score
        assert "score" in score
        assert "bars" in score
        assert "bins" in score


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

    data = response.json()
    assert len(data) == 3
    assert data["left"]["count"] == 0
    assert data["right"]["count"] == 2


@pytest.mark.parametrize("data", [
    {
        "score": "t4c8_score",
        "min": 1.5,
    },
    {
        "score": "t4c8_score",
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": "non-float-value",
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": 1.5,
        "max": "non-float-value",
    },
    {
        "score": "t4c8_score",
        "min": None,
        "max": 5.0,
    },
    {
        "score": "t4c8_score",
        "min": 1.5,
        "max": None,
    },
])
def test_gene_scores_partitions_bad_request(
    user_client: Client,
    data: dict[str, str | float | None],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/partitions"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 400


def test_gene_score_download(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/download/t4c8_score"

    response = user_client.get(url)
    assert response.status_code == 200
    content = list(response.streaming_content)  # type: ignore
    assert len(content) > 0
    assert len(content[0].decode().split("\t")) == 2

    # This is due to a bug that downloaded empty list
    # the second time that request has been made

    response = user_client.get(url)
    assert response.status_code == 200
    assert len(list(response.streaming_content)) > 0  # type: ignore
