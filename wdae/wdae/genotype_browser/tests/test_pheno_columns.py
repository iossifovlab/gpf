import json

import pytest
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")

QUERY_URL = "/api/v3/genotype_browser/query"


def test_query_preview_have_pheno_column_values(
    db, admin_client, preview_sources,
):
    data = {
        "datasetId": "quads_f1",
        "sources": preview_sources,
    }
    response = admin_client.post(
        QUERY_URL, json.dumps(data), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 3

    for row in enumerate(res):
        for value in row[-4:]:
            assert value is not None
