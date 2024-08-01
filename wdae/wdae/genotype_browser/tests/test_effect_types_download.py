# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import operator
from typing import Any

from django.test import Client
from rest_framework import status


def test_effect_details_download(
    admin_client: Client,
    datasets: Any,  # noqa: ARG001
) -> None:
    data = {
        "datasetId": "iossifov_2014",
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
        "NM_001348758:C2orf42:missense:439/574(Asn->Ser)|"
        "NM_001348763:C2orf42:missense:439/574(Asn->Ser)|"
        "NM_001348764:C2orf42:missense:439/574(Asn->Ser)|"
        "NR_145971:C2orf42:non-coding-intron:None/None[None]|"
        "NR_145972:C2orf42:non-coding:None|"
        "NM_001348759:C2orf42:missense:439/574(Asn->Ser)|"
        "NM_017880:C2orf42:missense:439/574(Asn->Ser)|"
        "NR_145967:C2orf42:non-coding-intron:None/None[None]|"
        "NR_145968:C2orf42:non-coding:None|"
        "NR_145969:C2orf42:non-coding-intron:None/None[None]|"
        "NM_001348760:C2orf42:missense:439/574(Asn->Ser)|"
        "NM_001348761:C2orf42:missense:439/574(Asn->Ser)|"
        "NM_001348762:C2orf42:missense:439/574(Asn->Ser)|"
        "NR_145970:C2orf42:non-coding:None",

        "NM_001348758:C2orf42:missense:557/574(Pro->Ser)|"
        "NM_001348763:C2orf42:missense:557/574(Pro->Ser)|"
        "NM_001348764:C2orf42:missense:557/574(Pro->Ser)|"
        "NR_145971:C2orf42:non-coding:None|"
        "NR_145972:C2orf42:non-coding:None|"
        "NM_001348759:C2orf42:missense:557/574(Pro->Ser)|"
        "NM_017880:C2orf42:missense:557/574(Pro->Ser)|"
        "NR_145967:C2orf42:non-coding:None|"
        "NR_145968:C2orf42:non-coding:None|"
        "NR_145969:C2orf42:non-coding:None|"
        "NM_001348760:C2orf42:missense:557/574(Pro->Ser)|"
        "NM_001348761:C2orf42:missense:557/574(Pro->Ser)|"
        "NM_001348762:C2orf42:missense:557/574(Pro->Ser)|"
        "NR_145970:C2orf42:non-coding:None",
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
