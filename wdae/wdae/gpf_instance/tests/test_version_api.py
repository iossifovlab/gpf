# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path

import pytest
import pytest_mock
from django.test import Client
from rest_framework import status

from gpf_instance.gpf_instance import WGPFInstance


@pytest.fixture()
def mock_instance(
    mocker: pytest_mock.MockerFixture,
    t4c8_wgpf_instance: WGPFInstance,
    tmp_path: Path,
) -> WGPFInstance:
    main_path = Path(tmp_path, "main_description.md")
    main_path.write_text("main description")
    mocker.patch.object(
        t4c8_wgpf_instance,
        "get_main_description_path",
        return_value=main_path,
    )

    about_path = Path(tmp_path, "about_description.md")
    about_path.write_text("about description")
    mocker.patch.object(
        t4c8_wgpf_instance,
        "get_about_description_path",
        return_value=about_path,
    )
    return t4c8_wgpf_instance


def test_get_gpf_version(
    mock_instance: WGPFInstance,  # noqa: ARG001
    anonymous_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/version"

    response = anonymous_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("version") is not None


def test_update_gpf_main_description_anonymous(
    mock_instance: WGPFInstance,  # noqa: ARG001
    anonymous_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/description"

    response = anonymous_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_gpf_main_description(
    mock_instance: WGPFInstance,  # noqa: ARG001
    admin_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/description"

    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("content") == "main description"

    response = admin_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_200_OK

    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("content") == "blagalkebgab"


def test_update_gpf_about_description_anonymous(
    mock_instance: WGPFInstance,  # noqa: ARG001
    anonymous_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/about"

    response = anonymous_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_gpf_about_description(
    mock_instance: WGPFInstance,  # noqa: ARG001
    admin_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/about"

    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("content") == "about description"

    response = admin_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_200_OK

    response = admin_client.get(url)
    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("content") == "blagalkebgab"
