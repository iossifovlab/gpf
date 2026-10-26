# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""The dataset gate checks every dataset id that a request names."""
import json

import pytest
from django.contrib.auth.models import User
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from datasets_api.permissions import add_group_perm_to_user

ALLOWED = "t4c8_study_2"
RESTRICTED = "t4c8_study_1"


@pytest.fixture
def allowed_user_client(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> Client:
    add_group_perm_to_user(ALLOWED, user)
    return user_client


@pytest.mark.parametrize("method,url", [
    ("get", f"/api/v3/families/{RESTRICTED}"),
    ("get", f"/api/v3/families/{RESTRICTED}/all"),
    ("get", f"/api/v3/families/{RESTRICTED}/f1.1"),
    ("get", f"/api/v3/families/{RESTRICTED}/f1.1/members"),
    ("get", f"/api/v3/families/{RESTRICTED}/f1.1/members/all"),
    ("get", f"/api/v3/families/{RESTRICTED}/f1.1/members/dad1"),
    ("get", f"/api/v3/common_reports/studies/{RESTRICTED}/full"),
    ("get", f"/api/v3/common_reports/families_data/{RESTRICTED}"),
    ("post", f"/api/v3/common_reports/families_data/{RESTRICTED}"),
])
def test_query_dataset_id_does_not_override_url_dataset_id(
    allowed_user_client: Client, method: str, url: str,
) -> None:
    response = getattr(allowed_user_client, method)(
        f"{url}?dataset_id={ALLOWED}",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("method,url,view_key,other_key", [
    ("post", "/api/v3/measures/partitions", "datasetId", "dataset_id"),
    ("post", "/api/v3/pheno_tool/people_values", "datasetId", "dataset_id"),
    ("get", "/api/v3/pheno_tool/measure", "datasetId", "dataset_id"),
    ("get", "/api/v3/pheno_tool/measures", "datasetId", "dataset_id"),
    ("get", "/api/v3/pheno_tool/instruments", "datasetId", "dataset_id"),
    ("get", "/api/v3/gene_view/config", "datasetId", "dataset_id"),
    ("post", "/api/v3/common_reports/family_counters", "study_id", "datasetId"),
])
def test_second_dataset_id_in_query_is_refused(
    allowed_user_client: Client,
    method: str, url: str, view_key: str, other_key: str,
) -> None:
    query = f"?{other_key}={ALLOWED}"
    if method == "get":
        response = allowed_user_client.get(
            f"{url}{query}&{view_key}={RESTRICTED}",
        )
    else:
        response = allowed_user_client.post(
            f"{url}{query}",
            json.dumps({view_key: RESTRICTED}),
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("method,url,view_key,other_key", [
    ("post", "/api/v3/genotype_browser/query", "datasetId", "dataset_id"),
    (
        "post", "/api/v3/genotype_browser/query-download",
        "datasetId", "dataset_id",
    ),
    ("get", "/api/v3/pheno_browser/measures_count", "dataset_id", "datasetId"),
    ("get", "/api/v3/pheno_browser/download", "dataset_id", "datasetId"),
])
def test_second_dataset_id_in_query_is_still_refused(
    allowed_user_client: Client,
    method: str, url: str, view_key: str, other_key: str,
) -> None:
    """Keep the 403 of the routes that refused a second id before.

    The genotype browser views check the dataset themselves. The old
    gate already read ``dataset_id`` first, the key of the pheno browser
    views. These cases pin the kept behaviour, not the conflict check.
    """
    query = f"?{other_key}={ALLOWED}"
    if method == "get":
        response = allowed_user_client.get(
            f"{url}{query}&{view_key}={RESTRICTED}",
        )
    else:
        response = allowed_user_client.post(
            f"{url}{query}",
            json.dumps({view_key: RESTRICTED}),
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("url,query_data", [
    (
        "/api/v3/common_reports/family_counters/download",
        {"study_id": RESTRICTED, "group_name": "Phenotype", "counter_id": "0"},
    ),
    (
        "/api/v3/pheno_tool/download",
        {
            "datasetId": RESTRICTED,
            "measureId": "i1.m1",
            "normalizeBy": [],
            "presentInParent": {"presentInParent": ["neither"]},
            "effectTypes": ["missense"],
        },
    ),
])
def test_dataset_id_in_query_data_is_compared_with_top_level_id(
    allowed_user_client: Client, url: str, query_data: dict,
) -> None:
    """Refuse a ``queryData`` dataset id that differs from the top level.

    Only the ``family_counters/download`` case pins the conflict check.
    The ``pheno_tool/download`` view checks ``queryData.datasetId``
    itself and answers 403 without the gate, so that case pins the kept
    behaviour, not the conflict check.
    """
    response = allowed_user_client.post(
        url,
        json.dumps({
            "dataset_id": ALLOWED,
            "queryData": json.dumps(query_data),
        }),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_two_dataset_ids_in_body_are_refused(
    allowed_user_client: Client,
) -> None:
    response = allowed_user_client.post(
        "/api/v3/measures/partitions",
        json.dumps({
            "dataset_id": ALLOWED,
            "datasetId": RESTRICTED,
            "measure": "i1.m1",
        }),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("url", [
    f"/api/v3/families/{RESTRICTED}/all",
    f"/api/v3/common_reports/studies/{RESTRICTED}/full",
])
def test_agreeing_dataset_ids_are_allowed(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
    url: str,
) -> None:
    add_group_perm_to_user(RESTRICTED, user)

    response = user_client.get(f"{url}?dataset_id={RESTRICTED}")

    assert response.status_code == status.HTTP_200_OK


def test_two_different_allowed_dataset_ids_are_refused(
    user: User,
    allowed_user_client: Client,
) -> None:
    add_group_perm_to_user(RESTRICTED, user)

    response = allowed_user_client.get(
        f"/api/v3/families/{RESTRICTED}/all?dataset_id={ALLOWED}",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
