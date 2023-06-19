# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json
import pytest

from rest_framework import status  # type: ignore


QUERY_URL = "/api/v3/genotype_browser/query"

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_simple_query_variants_preview(db, admin_client):
    data = {
        "datasetId": "TEST_REMOTE_iossifov_2014",
        "sources": [
            {"source": "location"},
            # {"source": "carrier_person_attributes"}
        ]
    }

    response = admin_client.post(
        QUERY_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = json.loads(
        "".join(map(lambda x: x.decode("utf-8"), response.streaming_content))
    )
    assert len(res) == 16
