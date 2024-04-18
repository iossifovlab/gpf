# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from collections.abc import Generator

import pytest
from django.test import Client
from rest_framework import status

from gpf_instance.gpf_instance import WGPFInstance


@pytest.fixture()
def reset_main_description(
    wdae_gpf_instance: WGPFInstance,
    global_dae_fixtures_dir: str,
) -> Generator[None, None, None]:
    file_path = os.path.join(global_dae_fixtures_dir, "main_description.md")
    with open(file_path, "r") as infile:
        content = infile.read()
    yield None
    with open(file_path, "w") as infile:
        infile.write(content)


@pytest.fixture()
def reset_about_description(
    wdae_gpf_instance: WGPFInstance,
    global_dae_fixtures_dir: str,
) -> Generator[None, None, None]:
    file_path = os.path.join(global_dae_fixtures_dir, "about_description.md")
    with open(file_path, "r") as infile:
        content = infile.read()
    yield None
    with open(file_path, "w") as infile:
        infile.write(content)


def test_get_gpf_version(
    anonymous_client: Client,
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/version"

    response = anonymous_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("version") is not None


def test_update_gpf_main_description_anonymous(
    anonymous_client: Client,
    reset_main_description: Generator[None, None, None],
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/description"

    response = anonymous_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_gpf_main_description(
    admin_client: Client,
    reset_main_description: Generator[None, None, None],
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
    anonymous_client: Client,
    reset_about_description: Generator[None, None, None],
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/about"

    response = anonymous_client.post(url, {"content": "blagalkebgab"})
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_gpf_about_description(
    admin_client: Client,
    reset_about_description: Generator[None, None, None],
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
