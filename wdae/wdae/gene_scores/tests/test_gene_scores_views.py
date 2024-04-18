# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Optional, Union

import pytest
from django.test.client import Client

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_gene_scores_list_view(user_client: Client) -> None:
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    print([d["score"] for d in data])
    assert len(data) == 5

    for score in data:
        assert "desc" in score
        assert "score" in score
        assert "bars" in score
        assert "bins" in score


def test_gene_scores_get_genes_view(user_client: Client) -> None:
    url = "/api/v3/gene_scores/genes"
    data = {
        "score": "LGD_rank",
        "min": 1.5,
        "max": 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 200

    assert len(response.json()) == 3


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

    data = response.json()
    assert len(data) == 3
    assert data["left"]["count"] == 1  # type: ignore
    assert data["right"]["count"] == 18454  # type: ignore


@pytest.mark.parametrize("data", [
    {
        "score": "LGD_rank",
        "min": 1.5,
    },
    {
        "score": "LGD_rank",
        "max": 5.0,
    },
    {
        "score": "LGD_rank",
        "min": "non-float-value",
        "max": 5.0,
    },
    {
        "score": "LGD_rank",
        "min": 1.5,
        "max": "non-float-value",
    },
    {
        "score": "LGD_rank",
        "min": None,
        "max": 5.0,
    },
    {
        "score": "LGD_rank",
        "min": 1.5,
        "max": None,
    },
])
def test_gene_scores_partitions_bad_request(
    user_client: Client, data: dict[str, Optional[Union[str, float]]],
) -> None:
    url = "/api/v3/gene_scores/partitions"
    response = user_client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == 400


def test_gene_score_download(user_client: Client) -> None:
    url = "/api/v3/gene_scores/download/LGD_rank"

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
