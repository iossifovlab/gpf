# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from rest_framework import status  # type: ignore

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


MEASURES_URL = "/api/v3/measures/type"
REGRESSIONS_URL = "/api/v3/measures/regressions"


@pytest.mark.parametrize("url,method,body", [
    (f"{MEASURES_URL}/continuous?datasetId=quads_f1", "get", None),
    (f"{REGRESSIONS_URL}?datasetId=comp", "get", None),
])
def test_measures_api_permissions(anonymous_client, url, method, body):
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_measures_list_categorical(admin_client):
    response = admin_client.get(
        f"{MEASURES_URL}/categorical?datasetId=quads_f1",
    )

    assert response.status_code == 200
    assert len(response.data) == 1


def test_measures_list_continuous(admin_client):
    response = admin_client.get(
        f"{MEASURES_URL}/continuous?datasetId=quads_f1",
    )

    assert response.status_code == 200
    assert len(response.data) == 1


def test_regressions(admin_client):
    response = admin_client.get(f"{REGRESSIONS_URL}?datasetId=comp")
    assert response.status_code == 200
    assert "age" in response.data
    assert "iq" in response.data


def test_measures_list_wrong_request(admin_client):
    response = admin_client.post("/api/v3/measures/histogram", {
        "datasetId": "comp", "measure": "i1.age",
    })
    assert response.status_code == 200

    response = admin_client.post("/api/v3/measures/histogram", {
        "datasetId": "comp", "measure": "asian",
    })
    assert response.status_code == 400
