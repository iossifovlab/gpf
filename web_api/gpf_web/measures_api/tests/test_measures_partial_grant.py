# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any

import pytest
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth.models import User
from django.test.client import Client
from rest_framework import status

PARTITIONS_URL = "/api/v3/measures/partitions"


def _partitions(client: Client, dataset_id: str, measure_id: str) -> Any:
    return client.post(
        PARTITIONS_URL,
        json.dumps({
            "datasetId": dataset_id,
            "measure": measure_id,
            "min": None,
            "max": None,
        }),
        content_type="application/json",
    )


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_partitions_of_an_allowed_leaf_under_partial_grant(
    user_client: Client,
) -> None:
    response = _partitions(user_client, "pheno_group", "i1.age")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["mid"]["count"] == 16


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_partitions_of_another_leaf_under_partial_grant_are_hidden(
    user_client: Client,
) -> None:
    response = _partitions(user_client, "pheno_group", "sib.age")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("grant_on_t4c8_study_1", "pheno_group_instance")
def test_partitions_of_a_genotype_parent_under_partial_grant(
    user_client: Client,
) -> None:
    allowed = _partitions(user_client, "pheno_parent", "i1.age")
    hidden = _partitions(user_client, "pheno_parent", "thr.score")

    assert allowed.status_code == status.HTTP_200_OK
    assert hidden.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("dataset_id", ["pheno_group", "pheno_parent"])
@pytest.mark.usefixtures("pheno_group_instance")
def test_partitions_under_a_grant_on_the_parent(
    user: User,
    user_client: Client,
    dataset_id: str,
) -> None:
    add_group_perm_to_user(dataset_id, user)

    response = _partitions(user_client, dataset_id, "thr.score")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["mid"]["count"] == 3
