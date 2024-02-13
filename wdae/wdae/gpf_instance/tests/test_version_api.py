import pytest
from rest_framework import status
from django.test import Client


@pytest.mark.django_db
def test_get_gpf_version(
    anonymous_client: Client
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/version"

    response = anonymous_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("version") is not None

@pytest.mark.django_db
def test_get_gpf_description(
    anonymous_client: Client
) -> None:
    """Try to get gpf version."""
    url = "/api/v3/instance/description"

    response = anonymous_client.get(url)

    assert response.status_code is status.HTTP_200_OK
    assert response.json().get("description") is not None
