# pylint: disable=W0621,C0114,C0116,W0212,W0613
import csv
import io
import json
from datetime import timedelta
from typing import Any

import pytest
import pytest_mock
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import timezone
from gpf_instance.gpf_instance import WGPFInstance
from oauth2_provider.models import Application, get_access_token_model
from rest_framework import status

from datasets_api.permissions import add_group_perm_to_user
from gpf.pheno.pheno_data import PhenotypeGroup


@pytest.fixture
def fully_granted_client(
    oauth_app: Application,
) -> Client:
    other = get_user_model().objects.create(
        email="other@example.com",
        name="Other",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    other.set_password("secret")
    other.save()
    add_group_perm_to_user("t4c8_dataset", other)  # type: ignore[arg-type]
    get_access_token_model()(
        user=other,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="other-token",  # ruff: ignore[hardcoded-password-func-arg]
        application=oauth_app,
    ).save()
    return Client(HTTP_AUTHORIZATION="Bearer other-token")


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_pedigree_under_partial_grant_matches_allowed_study(
    user_client: Client,
) -> None:
    expected = user_client.get(
        "/api/v3/datasets/pedigree/t4c8_study_2/family_id")

    response = user_client.get(
        "/api/v3/datasets/pedigree/t4c8_dataset/family_id")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected.json()
    assert set(response.json()["values_domain"]) == {"f2.1", "f2.3"}


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_pedigree_under_full_grant_serves_all_families(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/datasets/pedigree/t4c8_dataset/family_id")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.json()["values_domain"]) == {
        "f1.1", "f1.3", "f2.1", "f2.3",
    }


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_pedigree_etag_differs_between_partial_and_full_grant(
    user_client: Client,
    fully_granted_client: Client,
) -> None:
    url = "/api/v3/datasets/pedigree/t4c8_dataset/family_id"

    partial = user_client.get(url)
    full = fully_granted_client.get(url)

    assert partial.status_code == status.HTTP_200_OK
    assert full.status_code == status.HTTP_200_OK
    assert partial["ETag"] != full["ETag"]


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_families_data_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/common_reports/families_data/pheno_group")

    assert response.status_code == status.HTTP_200_OK
    rows = csv.DictReader(
        io.StringIO(b"".join(response.streaming_content).decode()),  # type: ignore
        delimiter="\t",
    )
    assert {row["familyId"] for row in rows} == {
        "f1.1", "f1.2", "f1.3", "f1.4",
    }


@pytest.mark.usefixtures("grant_on_study_1_pheno")
def test_families_data_of_a_remote_phenotype_child_is_403(
    user_client: Client,
    pheno_group_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    child = pheno_group_instance.get_wdae_wrapper("study_1_pheno")
    # A remote phenotype child carries no families that the server reads.
    mocker.patch.object(child, "is_remote", new=True)

    response = user_client.get(
        "/api/v3/common_reports/families_data/pheno_group")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def _people_values(client: Client, dataset_id: str, measure_id: str) -> Any:
    return client.post(
        "/api/v3/pheno_tool/people_values",
        json.dumps({"datasetId": dataset_id, "measureIds": [measure_id]}),
        content_type="application/json",
    )


@pytest.mark.usefixtures("pheno_group_instance")
def test_phenotype_data_under_a_grant_on_a_child_without_it_is_403(
    user: User,
    user_client: Client,
) -> None:
    add_group_perm_to_user("t4c8_study_2", user)

    response = _people_values(user_client, "pheno_parent", "i1.age")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("grant_on_study_1_pheno")
def test_phenotype_data_of_a_remote_phenotype_child_is_403(
    user_client: Client,
    pheno_group_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    child = pheno_group_instance.get_wdae_wrapper("study_1_pheno")
    mocker.patch.object(child, "is_remote", new=True)

    response = _people_values(user_client, "pheno_group", "i1.age")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("grant_on_study_1_pheno")
def test_registry_group_keeps_its_children_after_a_partial_grant_request(
    user: User,
    user_client: Client,
    pheno_group_instance: WGPFInstance,
) -> None:
    # A grant on two of the three leaves builds a restricted group.
    add_group_perm_to_user("sibling_pheno", user)

    response = _people_values(user_client, "pheno_group", "i1.age")

    group = pheno_group_instance.get_phenotype_data("pheno_group")
    wrapper = pheno_group_instance.get_wdae_wrapper("pheno_group")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(group, PhenotypeGroup)
    assert [child.pheno_id for child in group.children] == [
        "study_1_pheno", "sibling_pheno", "third_pheno"]
    assert wrapper is not None
    assert wrapper.phenotype_data is group
