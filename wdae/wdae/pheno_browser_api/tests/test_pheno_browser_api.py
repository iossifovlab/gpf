# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURES_INFO_URL = "/api/v3/pheno_browser/measures_info"
MEASURE_DESCRIPTION_URL = "/api/v3/pheno_browser/measure_description"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"


@pytest.mark.parametrize("url,method,body", [
    (f"{URL}?dataset_id=quads_f1_ds", "get", None),
    (f"{MEASURES_INFO_URL}?dataset_id=quads_f1_ds", "get", None),
    (
        f"{MEASURES_URL}?dataset_id=quads_f1_ds&instrument=instrument1", 
        "get", 
        None
    ),
    (
        DOWNLOAD_URL,
        "post",
        {
            "dataset_id": "quads_f1",
            "instrument": "instrument1"
        }
    ),
    (
        (
            f"{MEASURE_DESCRIPTION_URL}?dataset_id=quads_f1_ds"
            "&measure_id=instrument1.categorical"
        ),
        "get",
        None
    ),
])
def test_pheno_browser_api_permissions(anonymous_client, url, method, body):
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_instruments_missing_dataset_id(admin_client):
    response = admin_client.get(URL)

    assert response.status_code == 400


def test_instruments_missing_dataset_id_forbidden(user_client):
    response = user_client.get(URL)

    assert response.status_code == 400


def test_instruments(admin_client):
    url = "{}?dataset_id=quads_f1_ds".format(URL)
    response = admin_client.get(url)

    assert response.status_code == 200
    assert "default" in response.data
    assert "instruments" in response.data
    assert len(response.data["instruments"]) == 1


def test_instruments_forbidden(user_client):
    url = "{}?dataset_id=quads_f1_ds".format(URL)
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert (
        header["detail"]
        == "You do not have permission to perform this action."
    )


def test_measures_info(admin_client):
    url = f"{MEASURES_INFO_URL}?dataset_id=quads_f1_ds"
    response = admin_client.get(url)

    assert response.status_code == 200
    assert "base_image_url" in response.data
    assert "has_descriptions" in response.data


def test_measures(admin_client):
    url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
        MEASURES_URL
    )
    response = admin_client.get(url)
    assert response.status_code == 200

    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))
    assert len(res) == 4


def test_measures_forbidden(user_client, user):
    print(user.groups.all())
    url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
        MEASURES_URL
    )
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert (
        header["detail"]
        == "You do not have permission to perform this action."
    )


def test_download(admin_client):
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1"
    }
    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), "application/json"
    )

    assert response.status_code == 200

    header = list(response.streaming_content)[0].decode("utf-8")
    header = header.split()[0].split(",")
    assert header[0] == "person_id"


def test_download_specific_measures(admin_client):
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1",
        "measures": ["instrument1.continuous", "instrument1.categorical"]
    }
    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), "application/json"
    )

    assert response.status_code == 200

    content = list(response.streaming_content)[0].decode("utf-8")
    header = content.split()[0].split(",")
    assert len(header) == 3
    assert header[0] == "person_id"
    assert header[1] == "instrument1.continuous"
    assert header[2] == "instrument1.categorical"


def test_download_all_instruments(admin_client):
    data = {
        "dataset_id": "quads_f1"
    }
    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), "application/json"
    )

    assert response.status_code == 200

    header = list(response.streaming_content)[0].decode("utf-8")
    header = header.split()[0].split(",")

    print("header:\n", header)
    assert len(header) == 5
    assert set(header) == {
        "person_id",
        "instrument1.continuous",
        "instrument1.categorical",
        "instrument1.ordinal",
        "instrument1.raw",
    }


def test_download_all_instruments_specific_measures(admin_client):
    data = {
        "dataset_id": "quads_f1",
        "measures": ["instrument1.continuous", "instrument1.categorical"]
    }
    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), "application/json"
    )

    assert response.status_code == 200

    header = list(response.streaming_content)[0].decode("utf-8")
    header = header.split()[0].split(",")

    print("header:\n", header)
    assert len(header) == 3
    assert set(header) == {
        "person_id",
        "instrument1.continuous",
        "instrument1.categorical",
    }


def test_measure_details(admin_client):
    url = (
        "{}?dataset_id=quads_f1_ds&measure_id=instrument1.categorical"
        .format(MEASURE_DESCRIPTION_URL)
    )
    response = admin_client.get(url)

    assert response.status_code == 200

    print(response.data)
    assert response.data["instrument_name"] == "instrument1"
    assert response.data["measure_name"] == "categorical"
    assert response.data["measure_type"] == "categorical"
    assert response.data["values_domain"] == ["option1", "option2"]
