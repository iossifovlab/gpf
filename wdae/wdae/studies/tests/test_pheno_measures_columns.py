# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import cast

from django.http import StreamingHttpResponse
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


def test_study_with_phenotype_data(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    wrapper = t4c8_wgpf_instance.get_wdae_wrapper("t4c8_study_1")

    assert wrapper is not None
    assert wrapper.phenotype_data is not None


def test_pheno_measure_genotype_browser_columns(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:

    data = {
        "datasetId": "t4c8_study_1",
        "familyIds": ["f1.1"],
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.streaming
    assert isinstance(response, StreamingHttpResponse)
    streaming_response = cast(StreamingHttpResponse, response)

    content = streaming_response.getvalue()
    lines = json.loads(content.decode("utf-8"))

    assert len(lines) == 6

    for ln in lines:
        assert ln[0] == ["f1.1"]
        assert ln[-2] == ["166.340"]  # f1.1 p1 age
        assert ln[-1] == ["104.912"]  # f1.1 p1 IQ
