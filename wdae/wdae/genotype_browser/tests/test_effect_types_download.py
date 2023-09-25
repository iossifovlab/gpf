# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json
from rest_framework import status


def test_effect_details_download(admin_client, datasets) -> None:
    data = {
        "datasetId": "iossifov_2014",
        "effectTypes": ["missense"],
        "download": True,
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)

    header = res[0].decode("utf-8")[:-1].split("\t")
    assert len(res) == 3

    expected = [
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
        "NR_145970:C2orf42:non-coding:None"
    ]
    for index, row in enumerate(res[1:]):
        cols = row.decode("utf-8").strip().split("\t")
        assert len(cols) == len(header)

        line = dict(zip(header, cols))

        effect_details = line["effect details"]
        assert effect_details == expected[index]
