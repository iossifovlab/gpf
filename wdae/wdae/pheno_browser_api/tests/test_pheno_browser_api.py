# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any, cast

import pytest
import pytest_mock
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from rest_framework.response import Response
from users_api.models import User

from dae.pheno.pheno_data import PhenotypeStudy

URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURES_COUNT_URL = "/api/v3/pheno_browser/measures_count"
MEASURE_VALUES_URL = "/api/v3/pheno_browser/measure_values"
MEASURES_INFO_URL = "/api/v3/pheno_browser/measures_info"
MEASURE_DESCRIPTION_URL = "/api/v3/pheno_browser/measure_description"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"


@pytest.mark.parametrize("url,method,body,status", [
    (f"{URL}?dataset_id=t4c8_study_1", "get", None, status.HTTP_200_OK),
    (
        f"{MEASURES_INFO_URL}?dataset_id=t4c8_study_1",
        "get",
        None,
        status.HTTP_200_OK,
    ),
    (
        f"{MEASURES_URL}?dataset_id=t4c8_study_1&instrument=i1",
        "get",
        None,
        status.HTTP_200_OK,
    ),
    (
        DOWNLOAD_URL,
        "post",
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
        },
        status.HTTP_401_UNAUTHORIZED,
    ),
    (
        (
            f"{MEASURE_DESCRIPTION_URL}?dataset_id=t4c8_study_1"
            "&measure_id=i1.age"
        ),
        "get",
        None,
        status.HTTP_401_UNAUTHORIZED,
    ),
])
def test_pheno_browser_api_permissions(
    anonymous_client: Client,
    url: str,
    method: str,
    body: dict,
    status: Any,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json",
        )

    assert response
    assert response.status_code == status


def test_instruments_missing_dataset_id(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = admin_client.get(URL)

    assert response.status_code == 400


def test_instruments_missing_dataset_id_forbidden(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = user_client.get(URL)

    assert response.status_code == 400


def test_instruments(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = f"{URL}?dataset_id=t4c8_study_1"
    response = admin_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "default" in data
    assert "instruments" in data
    assert len(data["instruments"]) == 2


def test_anonymous_instruments_allowed(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = f"{URL}?dataset_id=t4c8_study_1"
    response = user_client.get(url)

    assert response.status_code == 200


def test_measures_info(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = f"{MEASURES_INFO_URL}?dataset_id=t4c8_study_1"
    response = admin_client.get(url)

    data = response.json()
    assert response.status_code == 200
    assert "base_image_url" in data
    assert "has_descriptions" in data


def test_measures(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = f"{MEASURES_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = admin_client.get(url)
    assert response.status_code == 200

    res = json.loads("".join([x.decode("utf-8") for x in response]))
    assert len(res) == 7


def test_measures_count(
    admin_client: Client,
    t4c8_wgpf: WGPFInstance,  # noqa: ARG001
) -> None:
    url = f"{MEASURES_COUNT_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = admin_client.get(url)
    assert response.status_code == 200
    res = response.json()

    assert res["count"] == 7


def test_anonymous_measures_allowed(
    user_client: Client,
    user: User,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    print(user.groups.all())
    url = f"{MEASURES_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = cast(Response, user_client.get(url))

    assert response.status_code == 200


def test_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(response.streaming_content)
    header = first_line.decode("utf-8")
    header = header.split()[0].split(",")
    assert header[0] == "person_id"


def test_download_specific_measures(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
        "search_term": "i1.age",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(response.streaming_content)
    content = first_line.decode("utf-8")
    header = content.split()[0].split(",")
    assert len(header) == 2
    assert header[0] == "person_id"
    assert header[1] == "i1.age"


def test_download_all_instruments(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "",
        "search_term": "",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(response.streaming_content)
    header = first_line.decode("utf-8")
    header = header.split()[0].split(",")

    print("header:\n", header)
    assert len(header) == 9
    assert set(header) == {
        "pheno_common.phenotype",
        "i1.age",
        "i1.iq",
        "i1.m1",
        "i1.m2",
        "i1.m3",
        "i1.m4",
        "i1.m5",
        "person_id",
    }


def test_download_all_instruments_specific_measures(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "search_term": "i1",
    }
    response = cast(Response, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(response.streaming_content)
    header = first_line.decode("utf-8")
    header = header.split()[0].split(",")

    print("header:\n", header)
    assert len(header) == 8
    assert set(header) == {
        "i1.age",
        "i1.iq",
        "i1.m1",
        "i1.m2",
        "i1.m3",
        "i1.m4",
        "i1.m5",
        "person_id",
    }


def test_measure_details(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = (
        f"{MEASURE_DESCRIPTION_URL}?dataset_id=t4c8_study_1"
        "&measure_id=i1.age"
    )
    response = admin_client.get(url)

    assert response.status_code == 200

    data = response.json()
    assert data["instrument_name"] == "i1"
    assert data["measure_name"] == "age"
    assert data["measure_type"] == "continuous"
    assert data["values_domain"] == [
        68.00148724003327,
        565.9100943623504,
    ]


def test_get_specific_measure_values(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
        "measure_ids": ["i1.age", "i1.iq"],
    }
    response = cast(Response, admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    ))

    assert response.status_code == 200
    content = json.loads(b"".join(list(response.streaming_content)))
    print(content)

    assert len(content) == 16

    assert content[0] == {
        "family_id": "f1.1",
        "person_id": "dad1",
        "role": "dad",
        "sex": "M",
        "status": "unaffected",
        "i1.age": pytest.approx(455.741, rel=1e-3),
        "i1.iq": pytest.approx(95.692, rel=1e-3),
    }
    assert content[1] == {
        "family_id": "f1.2",
        "person_id": "dad2",
        "role": "dad",
        "sex": "M",
        "status": "unaffected",
        "i1.age": pytest.approx(565.910, rel=1e-3),
        "i1.iq": pytest.approx(74.266, rel=1e-3),
    }


def test_get_measure_values(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = cast(Response, admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    ))

    assert response.status_code == 200
    content = json.loads(b"".join(list(response.streaming_content)))
    assert len(content) == 16
    assert content[0]["i1.age"] == pytest.approx(455.741, rel=1e-3)

    assert content[0] == {
        "family_id": "f1.1",
        "i1.age": pytest.approx(455.741, rel=1e-3),
        "i1.iq": pytest.approx(95.692, rel=1e-3),
        "i1.m1": pytest.approx(30.170, rel=1e-3),
        "i1.m2": pytest.approx(46.091, rel=1e-3),
        "i1.m3": pytest.approx(80.809, rel=1e-3),
        "i1.m4": 6.0,
        "i1.m5": "val5",
        "person_id": "dad1",
        "role": "dad",
        "sex": "M",
        "status": "unaffected",
    }
    assert content[2] == {
        "family_id": "f1.3",
        "i1.age": pytest.approx(529.034, rel=1e-3),
        "i1.iq": pytest.approx(102.329, rel=1e-3),
        "i1.m1": pytest.approx(102.991, rel=1e-3),
        "i1.m2": pytest.approx(49.505, rel=1e-3),
        "i1.m3": pytest.approx(74.830, rel=1e-3),
        "i1.m4": 2.0,
        "i1.m5": "val1",
        "person_id": "dad3",
        "role": "dad",
        "sex": "M",
        "status": "unaffected",
    }
    assert content[4] == {
        "family_id": "f1.1",
        "i1.age": pytest.approx(495.851, rel=1e-3),
        "i1.iq": pytest.approx(97.504, rel=1e-3),
        "i1.m1": pytest.approx(52.812, rel=1e-3),
        "i1.m2": pytest.approx(30.027, rel=1e-3),
        "i1.m3": pytest.approx(71.375, rel=1e-3),
        "i1.m4": 7.0,
        "i1.m5": "val3",
        "person_id": "mom1",
        "role": "mom",
        "sex": "F",
        "status": "unaffected",
    }


def test_measure_values_limits_measures(
    admin_client: Client,
    mocker: pytest_mock.MockerFixture,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data: dict[str, Any] = {
        "dataset_id": "t4c8_study_1",
    }
    data["measure_ids"] = [f"measure{i}" for i in range(2000)]
    spy = mocker.spy(PhenotypeStudy, "get_people_measure_values")

    admin_client.post(
        MEASURE_VALUES_URL, json.dumps(data), "application/json",
    )

    call_args = spy.call_args_list[-1][0]
    assert len(call_args[1]) == 1900
