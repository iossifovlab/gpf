# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json

import pytest
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/gene_view/config?datasetId=quads_f2", "get", None),
    (
        "/api/v3/gene_view/query_summary_variants",
        "post",
        {
            "datasetId": "quads_f2",
        },
    ),
    (
        "/api/v3/gene_view/download_summary_variants",
        "post",
        {
            "datasetId": "quads_f2",
        },
    ),
])
def test_gene_view_api_permissions(anonymous_client, url, method, body):
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_gene_view_summary_variants_query(db, admin_client):
    data = {
        "datasetId": "quads_f2",
    }

    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.data
    assert len(res) == 7
    for sv in res:
        assert len(sv["alleles"]) == 2


def test_gene_view_config(db, admin_client):
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=quads_f2",
    )
    assert response.status_code == status.HTTP_200_OK
    print(response.data)
