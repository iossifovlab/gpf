# pylint: disable=W0621,C0114,C0116,W0212,W0613
import copy
import json

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status  # type: ignore

TOOL_URL = "/api/v3/pheno_tool"
TOOL_DOWNLOAD_URL = "/api/v3/pheno_tool/download"

QUERY = {
    "datasetId": "t4c8_study_1",
    "measureId": "i1.m1",
    "normalizeBy": [],
    "presentInParent": {"presentInParent": ["neither"]},
    "effectTypes": ["missense", "frame-shift", "synonymous"],
}


@pytest.mark.parametrize("url,method,body", [
    (TOOL_URL, "post", QUERY),
    (TOOL_DOWNLOAD_URL, "post", QUERY),
    (
        "/api/v3/pheno_tool/people_values",
        "post",
        {
            "datasetId": "t4c8_study_1",
            "measureIds": ["i1.m1"],
        },
    ),
    (
        "/api/v3/pheno_tool/measure",
        "post",
        {
            "datasetId": "t4c8_study_1",
            "measureId": "i1.m1",
        },
    ),
    (
        "/api/v3/pheno_tool/measures?datasetId=t4c8_study_1&instrument=i1",
        "get", None,
    ),
    ("/api/v3/pheno_tool/instruments?datasetId=t4c8_study_1", "get", None),
])
def test_pheno_tool_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pheno_tool_view_valid_request(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_pheno_tool_view_missense(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    result = results[0]

    assert result["effect"] == "missense"
    assert result["maleResults"]["positive"]["count"] == 0
    assert result["maleResults"]["positive"]["deviation"] == 0
    assert result["maleResults"]["positive"]["mean"] == 0
    assert result["maleResults"]["negative"]["count"] == 0
    assert result["maleResults"]["negative"]["deviation"] == 0
    assert result["maleResults"]["negative"]["mean"] == 0
    assert result["femaleResults"]["positive"]["count"] == 1
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert result["femaleResults"]["positive"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert result["femaleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["negative"]["deviation"] == 0
    assert result["femaleResults"]["negative"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)


def test_pheno_tool_view_cnv_on_non_cnv_study(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense", "CNV+"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_pheno_tool_view_normalize(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    result = results[0]

    query["normalizeBy"] = [
        {"measure_name": "age", "instrument_name": "i1"}]  # type: ignore
    response_normalized = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response_normalized.status_code == status.HTTP_200_OK
    result_normalized = response_normalized.json()["results"][0]

    assert result["effect"] == "missense"
    assert result_normalized["effect"] == "missense"

    assert result["maleResults"]["negative"]["count"] == 0
    assert result_normalized["maleResults"]["negative"]["count"] == 0

    assert result["maleResults"]["negative"]["deviation"] == 0
    assert result_normalized["maleResults"]["negative"]["deviation"] == 0

    assert result["maleResults"]["negative"]["mean"] == 0

    assert result["femaleResults"]["negative"]["count"] == 1
    assert result_normalized["femaleResults"]["negative"]["count"] == 1

    assert result["femaleResults"]["negative"]["deviation"] == 0
    assert result_normalized["femaleResults"]["negative"]["deviation"] == 0

    assert result["femaleResults"]["negative"]["mean"] != pytest.approx(
        result_normalized["femaleResults"]["negative"]["mean"], abs=1e-3,
    )
    assert result["femaleResults"]["positive"]["mean"] != pytest.approx(
        result_normalized["femaleResults"]["positive"]["mean"], abs=1e-3,
    )


def test_pheno_tool_view_family_ids_filter(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["LGDs"]
    query["familyIds"] = ["f1.1", "f1.3"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["maleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["maleResults"]["negative"]["count"] == 0
    assert result["femaleResults"]["negative"]["count"] == 2


def test_pheno_tool_view_na_values(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["frame-shift"]
    query["familyIds"] = ["f1.1"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]

    assert result["effect"] == "frame-shift"
    assert result["femaleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert (
        result["femaleResults"]["positive"]["mean"]
        == result["femaleResults"]["negative"]["mean"]
    )


def test_pheno_tool_view_pheno_filter(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["frame-shift"]
    query["familyFilters"] = [
        {  # type: ignore
            "id": "Proband Continuous",
            "from": "phenodb",
            "source": "i1.m4",
            "sourceType": "continuous",
            "role": "prb",
            "selection": {
                "domainMax": 15,
                "domainMin": 1,
                "max": 15,
                "min": 1,
            },
        },
    ]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]

    assert result["effect"] == "frame-shift"
    assert result["femaleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert (
        result["femaleResults"]["positive"]["mean"]
        == result["femaleResults"]["negative"]["mean"]
    )
    assert result["maleResults"]["negative"]["count"] == 0
    assert result["maleResults"]["positive"]["count"] == 0
    assert (
        result["maleResults"]["positive"]["mean"]
        == result["maleResults"]["negative"]["mean"]
    )


def test_pheno_tool_view_missing_dataset(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["datasetId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pheno_tool_view_missing_measure(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["measureId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pheno_tool_download_valid_request(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense"]
    query["normalizeBy"] = [
        {"measure_name": "age", "instrument_name": "i1"}]  # type: ignore

    query = {"queryData": json.dumps(query)}
    response = admin_client.post(
        TOOL_DOWNLOAD_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    content = list(response.streaming_content)  # type: ignore
    assert content == [
        b"",
        (
            b"person_id,family_id,status,sex,"
            b"i1.m1,i1.age,i1.m1 ~ i1.age,missense\n"
        ),
        b"p1,f1.1,affected,F,110.71113,166.33975,1e-05,1.0\n",
        b"p3,f1.3,affected,F,96.63452,68.00149,1e-05,0.0\n",
    ]
