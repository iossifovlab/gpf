# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any, cast

import pytest
import pytest_mock
from django.test import Client
from rest_framework import status
from rest_framework.response import Response
from users_api.models import User

from dae.pheno.pheno_data import PhenotypeStudy

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURE_VALUES_URL = "/api/v3/pheno_browser/measure_values"
MEASURES_INFO_URL = "/api/v3/pheno_browser/measures_info"
MEASURE_DESCRIPTION_URL = "/api/v3/pheno_browser/measure_description"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"


@pytest.mark.parametrize("url,method,body", [
    (f"{URL}?dataset_id=quads_f1_ds", "get", None),
    (f"{MEASURES_INFO_URL}?dataset_id=quads_f1_ds", "get", None),
    (
        f"{MEASURES_URL}?dataset_id=quads_f1_ds&instrument=instrument1",
        "get",
        None,
    ),
    (
        DOWNLOAD_URL,
        "post",
        {
            "dataset_id": "quads_f1",
            "instrument": "instrument1",
        },
    ),
    (
        (
            f"{MEASURE_DESCRIPTION_URL}?dataset_id=quads_f1_ds"
            "&measure_id=instrument1.categorical"
        ),
        "get",
        None,
    ),
])
def test_pheno_browser_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict,
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_instruments_missing_dataset_id(admin_client: Client) -> None:
    response = admin_client.get(URL)

    assert response.status_code == 400


def test_instruments_missing_dataset_id_forbidden(user_client: Client) -> None:
    response = user_client.get(URL)

    assert response.status_code == 400


def test_instruments(admin_client: Client) -> None:
    url = f"{URL}?dataset_id=quads_f1_ds"
    response = admin_client.get(url)

    assert response.status_code == 200
    assert "default" in response.data
    assert "instruments" in response.data
    assert len(response.data["instruments"]) == 1


def test_instruments_forbidden(user_client: Client) -> None:
    url = f"{URL}?dataset_id=quads_f1_ds"
    response = user_client.get(url)

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert (
        header["detail"]
        == "You do not have permission to perform this action."
    )


def test_measures_info(admin_client: Client) -> None:
    url = f"{MEASURES_INFO_URL}?dataset_id=quads_f1_ds"
    response = admin_client.get(url)

    assert response.status_code == 200
    assert "base_image_url" in response.data
    assert "has_descriptions" in response.data


def test_measures(admin_client: Client) -> None:
    url = f"{MEASURES_URL}?dataset_id=quads_f1_ds&instrument=instrument1"
    response = admin_client.get(url)
    assert response.status_code == 200

    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))
    assert len(res) == 4


def test_measures_forbidden(user_client: Client, user: User) -> None:
    print(user.groups.all())
    url = f"{MEASURES_URL}?dataset_id=quads_f1_ds&instrument=instrument1"
    response = cast(Response, user_client.get(url))

    assert response.status_code == 403

    header = response.data
    assert len(header.keys()) == 1
    assert (
        header["detail"]
        == "You do not have permission to perform this action."
    )


def test_download(admin_client: Client) -> None:
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    header = list(response.streaming_content)[0].decode("utf-8")
    header = header.split()[0].split(",")
    assert header[0] == "person_id"


def test_download_specific_measures(admin_client: Client) -> None:
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1",
        "search_term": "instrument1.continuous",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    content = list(response.streaming_content)[0].decode("utf-8")
    header = content.split()[0].split(",")
    assert len(header) == 2
    assert header[0] == "person_id"
    assert header[1] == "instrument1.continuous"


def test_download_all_instruments(admin_client: Client) -> None:
    data = {
        "dataset_id": "quads_f1",
        "instrument": "",
        "search_term": "",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

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


def test_download_all_instruments_specific_measures(
    admin_client: Client,
) -> None:
    data = {
        "dataset_id": "quads_f1",
        "search_term": "instrument1",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

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


def test_measure_details(admin_client: Client) -> None:
    url = (
        f"{MEASURE_DESCRIPTION_URL}?dataset_id=quads_f1_ds"
        "&measure_id=instrument1.categorical"
    )
    response = admin_client.get(url)

    assert response.status_code == 200

    print(response.data)
    assert response.data["instrument_name"] == "instrument1"
    assert response.data["measure_name"] == "categorical"
    assert response.data["measure_type"] == "categorical"
    assert response.data["values_domain"] == ["option1", "option2"]


def test_get_specific_measure_values(admin_client: Client) -> None:
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1",
        "measure_ids": ["instrument1.continuous", "instrument1.categorical"],
    }
    response = cast(Response, admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    ))

    assert response.status_code == 200
    content = json.loads(b"".join(list(response.streaming_content)))

    assert content[0] == {
        "family_id": "f1",
        "person_id": "sib2",
        "role": "sib",
        "sex": "F",
        "status": "unaffected",
        "instrument1.continuous": 4.56,
        "instrument1.categorical": None,
    }
    assert content[1] == {
        "family_id": "f1",
        "person_id": "sib1",
        "role": "sib",
        "sex": "F",
        "status": "unaffected",
        "instrument1.continuous": 1.23,
        "instrument1.categorical": None,
    }


def test_get_measure_values(admin_client: Client) -> None:
    data = {
        "dataset_id": "quads_f1",
        "instrument": "instrument1",
    }
    response = cast(Response, admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    ))

    assert response.status_code == 200
    content = json.loads(b"".join(list(response.streaming_content)))

    assert len(content) == 5
    assert content[0] == {
        "family_id": "f1",
        "person_id": "sib2",
        "role": "sib",
        "sex": "F",
        "status": "unaffected",
        "instrument1.continuous": 4.56,
        "instrument1.categorical": None,
        "instrument1.ordinal": None,
        "instrument1.raw": None,
    }
    assert content[2] == {
        "family_id": "f1",
        "person_id": "prb1",
        "role": "prb",
        "sex": "M",
        "status": "affected",
        "instrument1.continuous": 3.14,
        "instrument1.categorical": "option2",
        "instrument1.ordinal": 5.0,
        "instrument1.raw": "somevalue",
    }
    assert content[4] == {
        "family_id": "f1",
        "person_id": "dad1",
        "role": "dad",
        "sex": "M",
        "status": "unaffected",
        "instrument1.continuous": 2.718,
        "instrument1.categorical": None,
        "instrument1.ordinal": None,
        "instrument1.raw": "othervalue",
    }


def test_measure_values_limits_measures(
    admin_client: Client,
    mocker: pytest_mock.MockerFixture,
) -> None:
    data: dict[str, Any] = {
        "dataset_id": "quads_f1",
    }
    data["measure_ids"] = [f"measure{i}" for i in range(2000)]
    spy = mocker.spy(PhenotypeStudy, "get_people_measure_values")

    admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    )

    call_args = spy.call_args_list[-1][0]
    assert len(call_args[1]) == 1900
