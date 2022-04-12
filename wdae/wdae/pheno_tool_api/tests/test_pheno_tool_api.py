import pytest

import copy
import json

from rest_framework import status  # type: ignore


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


def test_pheno_tool_view_valid_request(admin_client):
    query = copy.deepcopy(QUERY)

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_pheno_tool_view_missense(admin_client):
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["Missense"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.data["results"][0]
    assert len(response.data["results"]) == 1

    assert result["effect"] == "Missense"
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


def test_pheno_tool_view_normalize(admin_client):
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["Missense"]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.data["results"][0]

    query["normalizeBy"] = [{"measure_name": "age", "instrument_name": "i1"}]
    response_normalized = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response_normalized.status_code == status.HTTP_200_OK
    result_normalized = response_normalized.data["results"][0]

    assert result["effect"] == "Missense"
    assert result_normalized["effect"] == "Missense"

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


def test_pheno_tool_view_family_ids_filter(admin_client):
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
    result = response.data["results"][0]
    assert result["maleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["maleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["negative"]["count"] == 1


def test_pheno_tool_view_na_values(admin_client):
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
    result = response.data["results"][0]

    assert result["effect"] == "frame-shift"
    assert result["femaleResults"]["negative"]["count"] == 1
    assert result["femaleResults"]["positive"]["count"] == 0
    assert result["femaleResults"]["positive"]["deviation"] == 0
    assert (
        result["femaleResults"]["positive"]["mean"]
        == result["femaleResults"]["negative"]["mean"]
    )


def test_pheno_tool_view_pheno_filter(admin_client):
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["frame-shift"]
    query["familyFilters"] = [
        {
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
    result = response.data["results"][0]

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


def test_pheno_tool_view_missing_dataset(admin_client):
    query = copy.deepcopy(QUERY)
    query["datasetId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_pheno_tool_view_missing_measure(admin_client):
    query = copy.deepcopy(QUERY)
    query["measureId"] = "???"

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pheno_tool_download_valid_request(admin_client):
    query = copy.deepcopy(QUERY)
    query["effectTypes"] = ["Missense"]
    query["normalizeBy"] = [{"measure_name": "age", "instrument_name": "i1"}]

    response = admin_client.post(
        TOOL_URL,
        json.dumps(query),
        format="json",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["description"] == "i1.m1 ~ i1.age"
    assert response.data["results"]
    assert len(response.data["results"]) == 1

    result = response.data["results"][0]
    assert result["effect"] == "Missense"
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
