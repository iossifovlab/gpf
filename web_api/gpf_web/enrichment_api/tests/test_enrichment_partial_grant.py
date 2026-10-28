# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client
from rest_framework import status

QUERY = {
    "datasetId": "t4c8_dataset",
    "enrichmentBackgroundModel": "coding_len_background",
    "enrichmentCountingModel": "enrichment_gene_counting",
    "geneSymbols": ["T4", "C8"],
}


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_enrichment_test_under_partial_grant_is_forbidden(
    user_client: Client,
) -> None:
    response = user_client.post(
        "/api/v3/enrichment/test",
        json.dumps(QUERY), content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_enrichment_test_under_full_grant(
    user_client: Client,
) -> None:
    response = user_client.post(
        "/api/v3/enrichment/test",
        json.dumps(QUERY), content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.usefixtures("all_children_grant", "t4c8_wgpf_instance")
def test_enrichment_test_under_grant_on_all_child_studies(
    user_client: Client,
) -> None:
    response = user_client.post(
        "/api/v3/enrichment/test",
        json.dumps(QUERY), content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
