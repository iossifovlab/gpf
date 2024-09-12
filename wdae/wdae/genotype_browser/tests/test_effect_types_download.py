# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import operator

from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


def test_effect_details_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "effectTypes": ["missense"],
        "download": True,
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = "".join([
        p.decode("utf8")
        for p in response.streaming_content  # type: ignore
    ]).split("\n")
    res = [r for r in res if r]

    header = res[0][:-1].split("\t")
    assert len(res) == 3

    expected = [
        "tx1:c8:missense:13/14(Asp->Glu)",
        "tx1:c8:synonymous:13/14; tx1:c8:missense:13/14(Asp->Glu)",
    ]
    results = []
    for row in res[1:]:
        cols = row.strip().split("\t")
        assert len(cols) == len(header)

        results.append(dict(zip(header, cols, strict=True)))

    results = sorted(results, key=operator.itemgetter("effect details"))

    for line, expected_effect in zip(results, expected, strict=True):

        effect_details = line["effect details"]
        assert effect_details == expected_effect
