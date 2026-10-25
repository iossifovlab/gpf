# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_mock
from django.http import StreamingHttpResponse
from django.test import Client, override_settings
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from users_api.models import User

URL = "/api/v3/pheno_browser/instruments"
MEASURES_URL = "/api/v3/pheno_browser/measures"
MEASURES_COUNT_URL = "/api/v3/pheno_browser/measures_count"
MEASURES_INFO_URL = "/api/v3/pheno_browser/measures_info"
MEASURE_DESCRIPTION_URL = "/api/v3/pheno_browser/measure_description"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"
IMAGES_URL = "/api/v3/pheno_browser/images"


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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    response = admin_client.get(URL)

    assert response.status_code == 400


def test_instruments_missing_dataset_id_forbidden(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    response = user_client.get(URL)

    assert response.status_code == 400


def test_instruments(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    url = f"{URL}?dataset_id=t4c8_study_1"
    response = user_client.get(url)

    assert response.status_code == 200


def test_measures_info(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    url = f"{MEASURES_INFO_URL}?dataset_id=t4c8_study_1"
    response = admin_client.get(url)

    data = response.json()
    assert response.status_code == 200
    assert "base_image_url" in data
    assert "has_descriptions" in data


def test_measures(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    url = f"{MEASURES_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = admin_client.get(url)
    assert response.status_code == 200

    res = json.loads("".join([x.decode("utf-8") for x in response]))
    assert len(res) == 7


def test_measures_count(
    admin_client: Client,
    t4c8_wgpf: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    url = f"{MEASURES_COUNT_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = admin_client.get(url)
    assert response.status_code == 200
    res = response.json()

    assert res["count"] == 7


def test_anonymous_measures_allowed(
    user_client: Client,
    user: User,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    print(user.groups.all())
    url = f"{MEASURES_URL}?dataset_id=t4c8_study_1&instrument=i1"
    response = user_client.get(url)

    assert response.status_code == 200


def test_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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


@override_settings(FEATURE_FLAGS={"pheno_browser_download": False})
def test_download_disabled_returns_404(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    reset_flags: None,  # ruff: ignore[unused-function-argument]
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = admin_client.get(DOWNLOAD_URL, data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@override_settings(FEATURE_FLAGS={"pheno_browser_download": False})
def test_download_head_disabled_returns_404(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    reset_flags: None,  # ruff: ignore[unused-function-argument]
) -> None:
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = admin_client.head(DOWNLOAD_URL, data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@override_settings(FEATURE_FLAGS={})
def test_download_enabled_when_override_omits_flag(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    reset_flags: None,  # ruff: ignore[unused-function-argument]
) -> None:
    """An override that omits the flag leaves the download enabled."""
    data = {
        "dataset_id": "t4c8_study_1",
        "instrument": "i1",
    }
    response = cast(StreamingHttpResponse, admin_client.get(
        DOWNLOAD_URL, data,
    ))

    assert response.status_code == status.HTTP_200_OK


def test_measure_details(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
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


@pytest.fixture
def images_dir(
    tmp_path: Path,
    mocker: pytest_mock.MockerFixture,
) -> Path:
    """Configure a temporary phenotype images directory."""
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    (instance_dir / "gpf_instance.yaml").write_text(
        "instance_id: test_instance\n"
        f"phenotype_images: {tmp_path / 'images'}\n",
    )
    mocker.patch.dict(
        os.environ, {"DAE_DB_DIR": str(instance_dir), "GPF_CONF_DIR": ""})
    images = tmp_path / "images"
    (images / "i1").mkdir(parents=True)
    (images / "i1" / "i1.age.png").write_bytes(b"PNG data")
    (tmp_path / "outside.json").write_text("{}")
    return images


@pytest.mark.usefixtures("t4c8_wgpf_instance", "images_dir")
def test_image_inside_images_dir(
    admin_client: Client,
) -> None:
    response = admin_client.get(f"{IMAGES_URL}/t4c8_study_1/i1/i1.age.png")

    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"PNG data"


@pytest.mark.usefixtures("t4c8_wgpf_instance", "images_dir")
def test_image_parent_traversal_not_found(
    admin_client: Client,
) -> None:
    response = admin_client.get(f"{IMAGES_URL}/t4c8_study_1/../outside.json")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("t4c8_wgpf_instance")
def test_image_absolute_path_not_found(
    admin_client: Client,
    images_dir: Path,
) -> None:
    outside = images_dir.parent / "outside.json"

    response = admin_client.get(f"{IMAGES_URL}/t4c8_study_1/{outside}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("t4c8_wgpf_instance", "images_dir")
def test_image_missing_inside_images_dir_not_found(
    admin_client: Client,
) -> None:
    response = admin_client.get(f"{IMAGES_URL}/t4c8_study_1/i1/missing.png")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("t4c8_wgpf_instance", "images_dir")
@pytest.mark.parametrize("image_path", ["i1", "i1/", "."])
def test_image_directory_not_found(
    admin_client: Client,
    image_path: str,
) -> None:
    response = admin_client.get(f"{IMAGES_URL}/t4c8_study_1/{image_path}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
