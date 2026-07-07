# pylint: disable=W0621,C0114,C0116,W0212,W0613
from django.test import Client, override_settings
from rest_framework import status

from gpf_instance.gpf_instance import WGPFInstance


def test_features_endpoint_returns_flags(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    reset_flags: None,  # noqa: ARG001
) -> None:
    """The features endpoint advertises the flag registry."""
    response = anonymous_client.get("/api/v3/instance/features")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("pheno_browser_download") is True
    assert response.headers.get("ETag")


@override_settings(FEATURE_FLAGS={"pheno_browser_download": False})
def test_features_endpoint_reflects_overrides(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    reset_flags: None,  # noqa: ARG001
) -> None:
    """A settings override is reflected in the advertised flags."""
    response = anonymous_client.get("/api/v3/instance/features")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("pheno_browser_download") is False


@override_settings(FEATURE_FLAGS={})
def test_features_endpoint_merges_defaults(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    reset_flags: None,  # noqa: ARG001
) -> None:
    """A known flag keeps its coded default when not named in overrides."""
    response = anonymous_client.get("/api/v3/instance/features")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("pheno_browser_download") is True
