import pytest
import json
from rest_framework import status

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


def test_gene_view_summary_variants_query(db, admin_client):
    data = {
        "datasetId": "quads_f2",
    }

    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 7
    for v in res:
        assert len(v['alleles']) == 2


def test_gene_view_config(db, admin_client):
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=quads_f2"
    )
    assert response.status_code == status.HTTP_200_OK
    print(response.data)
