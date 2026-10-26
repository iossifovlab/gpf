# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""The views that serve dataset data check the access to that dataset."""
import json
from typing import Any

import pytest
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth.models import User
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

ALLOWED = "t4c8_study_2"
RESTRICTED = "t4c8_study_1"

ENRICHMENT_TEST_BODY = {
    "enrichmentBackgroundModel": "coding_len_background",
    "enrichmentCountingModel": "enrichment_gene_counting",
    "geneSymbols": ["T4", "C8"],
}

GATED_GET_URLS = [
    f"/api/v3/datasets/pedigree/{RESTRICTED}/person_id",
    f"/api/v3/person_sets/{RESTRICTED}/configs",
    f"/api/v3/person_sets/{RESTRICTED}/domain",
    f"/api/v3/person_sets/{RESTRICTED}/stats/phenotype",
]


@pytest.mark.parametrize("url", GATED_GET_URLS)
def test_anonymous_client_is_refused(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    url: str,
) -> None:
    response = anonymous_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("url", GATED_GET_URLS)
def test_user_without_grant_is_refused(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    url: str,
) -> None:
    response = user_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("url", GATED_GET_URLS)
def test_granted_user_is_served(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    url: str,
) -> None:
    add_group_perm_to_user(RESTRICTED, user)

    response = user_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("url", GATED_GET_URLS)
def test_query_dataset_id_of_allowed_dataset_is_refused(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    url: str,
) -> None:
    add_group_perm_to_user(ALLOWED, user)

    response = user_client.get(f"{url}?dataset_id={ALLOWED}")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def _post_enrichment_test(
    client: Client, dataset_id: str, query: str = "",
) -> Any:
    return client.post(
        f"/api/v3/enrichment/test{query}",
        json.dumps({"datasetId": dataset_id, **ENRICHMENT_TEST_BODY}),
        content_type="application/json",
    )


def test_enrichment_test_refuses_anonymous_client(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    response = _post_enrichment_test(anonymous_client, RESTRICTED)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_enrichment_test_refuses_user_without_grant(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    response = _post_enrichment_test(user_client, RESTRICTED)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_enrichment_test_serves_granted_user(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    add_group_perm_to_user(RESTRICTED, user)

    response = _post_enrichment_test(user_client, RESTRICTED)

    assert response.status_code == status.HTTP_200_OK


def test_enrichment_test_refuses_query_dataset_id_of_allowed_dataset(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> None:
    add_group_perm_to_user(ALLOWED, user)

    response = _post_enrichment_test(
        user_client, RESTRICTED, f"?dataset_id={ALLOWED}",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
