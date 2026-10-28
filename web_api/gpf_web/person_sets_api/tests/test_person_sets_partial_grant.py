# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from django.test.client import Client
from rest_framework import status


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_collection_stats_under_partial_grant_match_allowed_study(
    user_client: Client,
) -> None:
    expected = user_client.get(
        "/api/v3/person_sets/t4c8_study_2/stats/phenotype")

    response = user_client.get(
        "/api/v3/person_sets/t4c8_dataset/stats/phenotype")

    assert response.status_code == status.HTTP_200_OK
    assert expected.status_code == status.HTTP_200_OK
    assert response.json() == expected.json()


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_collection_stats_under_full_grant_count_all_studies(
    user_client: Client,
    admin_client: Client,
) -> None:
    expected = admin_client.get(
        "/api/v3/person_sets/t4c8_dataset/stats/phenotype")

    response = user_client.get(
        "/api/v3/person_sets/t4c8_dataset/stats/phenotype")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected.json()
