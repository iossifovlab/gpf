# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

QUERY_URL = "/api/v3/genotype_browser/query"


def test_query_preview_have_pheno_column_values(
    admin_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_study_1",
        "sources": preview_sources,
    }
    response = admin_client.post(
        QUERY_URL, json.dumps(data), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 12

    for row in enumerate(res):
        for value in row[-2:]:
            assert value is not None
