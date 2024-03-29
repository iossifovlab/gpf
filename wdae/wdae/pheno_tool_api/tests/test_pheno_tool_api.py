# pylint: disable=W0621,C0114,C0116,W0212,W0613
import copy
import json

import pytest

from rest_framework import status  # type: ignore
from django.test.client import Client


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


TOOL_URL = "/api/v3/pheno_tool"
TOOL_DOWNLOAD_URL = "/api/v3/pheno_tool/download"

QUERY = {
    "datasetId": "fake_study",
    "measureId": "i1.m1",
    "normalizeBy": [],
    "presentInParent": {"presentInParent": ["neither"]},
    "effectTypes": ["missense", "frame-shift", "synonymous"],
}


@pytest.mark.parametrize("url,method,body", [
    (TOOL_URL, "post", QUERY),
    (TOOL_DOWNLOAD_URL, "post", QUERY),
    (
        "/api/v3/pheno_tool/persons",
        "post",
        {
            "datasetId": "f1_trio",
        }
    ),
    (
        "/api/v3/pheno_tool/people_values",
        "post",
        {
            "datasetId": "f1_trio",
            "measureIds": ["i1.m1"]
        }
    ),
    (
        "/api/v3/pheno_tool/measure",
        "post",
        {
            "datasetId": "f1_trio",
            "measureId": "i1.m1"
        }
    ),
    (
        "/api/v3/pheno_tool/measures?datasetId=f1_trio&instrument=i1",
        "get", None
    ),
    ("/api/v3/pheno_tool/instruments?datasetId=f1_trio", "get", None),
])
def test_pheno_tool_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pheno_tool_view_valid_request(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_pheno_tool_view_missense(admin_client: Client) -> None:
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
    assert result["maleResults"]["positive"]["mean"] == \
        pytest.approx(59.2852, abs=1e-3)
    assert result["maleResults"]["negative"]["count"] == 2
    assert result["maleResults"]["negative"]["deviation"] == \
        pytest.approx(33.9863, abs=1e-3)
    assert result["maleResults"]["negative"]["mean"] == \
        pytest.approx(59.2852, abs=1e-3)
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert result["femaleResults"]["positive"]["mean"] == \
        pytest.approx(69.0976, abs=1e-3)
    assert result["femaleResults"]["negative"]["count"] == 2
    assert result["femaleResults"]["negative"]["deviation"] == \
        pytest.approx(7.9317, abs=1e-3)
    assert result["femaleResults"]["negative"]["mean"] == \
        pytest.approx(69.0976, abs=1e-3)


def test_pheno_tool_view_cnv_on_non_cnv_study(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense", "CNV+"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_pheno_tool_view_normalize(admin_client: Client) -> None:
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

    assert result["maleResults"]["negative"]["count"] == 2
    assert result_normalized["maleResults"]["negative"]["count"] == 2

    assert result["maleResults"]["negative"]["deviation"] == \
        pytest.approx(33.9863, abs=1e-3)
    assert result_normalized["maleResults"]["negative"]["deviation"] == \
        pytest.approx(31.3010, abs=1e-3)

    assert result["maleResults"]["negative"]["mean"] != pytest.approx(
        result_normalized["maleResults"]["negative"]["mean"], abs=1e-3
    )

    assert result["femaleResults"]["negative"]["count"] == 2
    assert result_normalized["femaleResults"]["negative"]["count"] == 2

    assert result["femaleResults"]["negative"]["deviation"] == \
        pytest.approx(7.9317, abs=1e-3)
    assert result_normalized["femaleResults"]["negative"]["deviation"] == \
        pytest.approx(12.5952, abs=1e-3)

    assert result["femaleResults"]["negative"]["mean"] != pytest.approx(
        result_normalized["femaleResults"]["negative"]["mean"], abs=1e-3
    )


def test_pheno_tool_view_family_ids_filter(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["LGDs"]
    query["familyIds"] = ["f1", "f4"]

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
    assert result["maleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["negative"]["count"] == 1


def test_pheno_tool_view_na_values(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["frame-shift"]
    query["familyIds"] = ["f4"]

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


def test_pheno_tool_view_pheno_filter(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["frame-shift"]
    query["familyFilters"] = [
        {  # type: ignore
            "id": "Proband Continuous",
            "from": "phenodb",
            "source": "i1.m2",
            "sourceType": "continuous",
            "role": "prb",
            "selection": {
                "domainMax": 67.4553055880587,
                "domainMin": 17.5536981163936,
                "max": 43,
                "min": 42.9,
            },
        }
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


def test_pheno_tool_view_missing_dataset(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["datasetId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pheno_tool_view_missing_measure(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["measureId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pheno_tool_download_valid_request(admin_client: Client) -> None:
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["missense"]
    query["normalizeBy"] = [
        {"measure_name": "age", "instrument_name": "i1"}]  # type: ignore

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] == "i1.m1 ~ i1.age"
    assert response.json()["results"]
    assert len(response.json()["results"]) == 1

    result = response.json()["results"][0]
    assert result["effect"] == "missense"
    assert result["maleResults"]["positive"]["count"] == 0
    assert result["maleResults"]["positive"]["deviation"] == 0
    assert result["maleResults"]["positive"]["mean"] == \
        pytest.approx(-6.0038, 1e-3)

    assert result["maleResults"]["negative"]["count"] == 2
    assert result["maleResults"]["negative"]["deviation"] == \
        pytest.approx(31.3010, 1e-3)
    assert result["maleResults"]["negative"]["mean"] == \
        pytest.approx(-6.0038, 1e-3)

    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert result["femaleResults"]["positive"]["mean"] == \
        pytest.approx(6.0038, 1e-3)

    assert result["femaleResults"]["negative"]["count"] == 2
    assert result["femaleResults"]["negative"]["deviation"] == \
        pytest.approx(12.5952, 1e-3)
    assert result["femaleResults"]["negative"]["mean"] == \
        pytest.approx(6.0038, 1e-3)
