import pytest
import json


pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURES_INFO_URL = "/api/v3/pheno_browser/measures_info"
MEASURE_DESCRIPTION_URL = "/api/v3/pheno_browser/measure_description"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"


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
    url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
        DOWNLOAD_URL
    )
    response = admin_client.get(url)

    assert response.status_code == 200

    header = response.content.decode("utf-8").split()[0].split(",")
    assert header[0] == "person_id"


def test_download_forbidden(user_client):
    url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
        DOWNLOAD_URL
    )
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert (
        header["detail"]
        == "You do not have permission to perform this action."
    )


def test_download_all_instruments(admin_client):
    url = "{}?dataset_id=quads_f1_ds&instrument=".format(DOWNLOAD_URL)
    response = admin_client.get(url)

    assert response.status_code == 200

    header = response.content.decode("utf-8").split()[0].split(",")

    print("header:\n", header)
    assert len(header) == 5
    assert set(header) == {
        "person_id",
        "instrument1.continuous",
        "instrument1.categorical",
        "instrument1.ordinal",
        "instrument1.raw",
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
