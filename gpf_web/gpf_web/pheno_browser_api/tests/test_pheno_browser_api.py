# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from collections.abc import Iterator
from typing import Any, cast

import pytest
from django.http import StreamingHttpResponse
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from users_api.models import User

URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURES_COUNT_URL = "/api/v3/pheno_browser/measures_count"
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
        status.HTTP_200_OK,
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
    response = user_client.get(url)

    assert response.status_code == 200


def test_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = cast(StreamingHttpResponse, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(cast(Iterator[bytes], response.streaming_content))
    header_line = first_line.decode("utf-8")
    header = header_line.split()[0].split(",")
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
    response = cast(StreamingHttpResponse, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(cast(Iterator[bytes], response.streaming_content))
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
    response = cast(StreamingHttpResponse, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(cast(Iterator[bytes], response.streaming_content))
    header_line = first_line.decode("utf-8")
    header = header_line.split()[0].split(",")

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
    response = cast(StreamingHttpResponse, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == 200

    first_line = next(cast(Iterator[bytes], response.streaming_content))
    header_line = first_line.decode("utf-8")
    header = header_line.split()[0].split(",")

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
