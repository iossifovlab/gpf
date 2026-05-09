# pylint: disable=W0621,C0114,C0116,W0212,W0613
from django.test import Client
from pytest_mock import MockerFixture
from rest_framework import status

from gpf_instance.gpf_instance import WGPFInstance


def test_genome_hg38(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        t4c8_wgpf_instance.reference_genome.resource,
        "resource_id",
        "hg38/reference_genome",
    )
    url = "/api/v3/instance/genome"

    response = admin_client.get(url)
    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data == {"build": "hg38"}


def test_genome_hg19(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        t4c8_wgpf_instance.reference_genome.resource,
        "resource_id",
        "hg19/reference_genome",
    )
    url = "/api/v3/instance/genome"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data == {"build": "hg19"}


def test_genome_other(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        t4c8_wgpf_instance.reference_genome.resource,
        "resource_id",
        "reference_genome",
    )
    url = "/api/v3/instance/genome"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data == {"build": "other"}
