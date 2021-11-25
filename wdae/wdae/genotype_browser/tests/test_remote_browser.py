import json
import pytest

from rest_framework import status


QUERY_URL = "/api/v3/genotype_browser/query"

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_simple_query_variants_preview(db, admin_client, remote_settings):
    data = {
        "datasetId": "TEST_REMOTE_iossifov_2014",
        "sources": [{"source": "location"}]
    }

    response = admin_client.post(
        QUERY_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = json.loads(
        "".join(map(lambda x: x.decode("utf-8"), response.streaming_content))
    )
    assert len(res) == 16
