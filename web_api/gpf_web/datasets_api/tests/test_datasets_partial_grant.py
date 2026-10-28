# pylint: disable=W0621,C0114,C0116,W0212,W0613
import csv
import io
import pathlib
import textwrap
from datetime import timedelta

import pytest
import pytest_mock
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import timezone
from gain.genomic_resources.testing import setup_directories, setup_pedigree
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from oauth2_provider.models import Application, get_access_token_model
from rest_framework import status
from utils.testing import setup_wgpf_instance

from datasets_api.permissions import add_group_perm_to_user
from gpf.pheno.pheno_import import main as pheno_import


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


@pytest.fixture(scope="module")
def pheno_group_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    """Build a phenotype group of ``study_1_pheno`` and a sibling study."""
    root_path = tmp_path_factory.mktemp("pheno_group")
    instance = setup_wgpf_instance(root_path)
    pheno_dir = pathlib.Path(instance.dae_dir) / "pheno"
    sibling_ped = setup_pedigree(
        root_path / "sibling_pheno" / "in.ped", """
familyId personId dadId momId sex status role
fx.1     momx     0     0     2   1      mom
fx.1     dadx     0     0     1   1      dad
fx.1     px       dadx  momx  2   2      prb
        """)
    instruments = root_path / "sibling_pheno" / "instruments"
    setup_directories(
        instruments, {
            "sib.csv": "personId,age\nmomx,40\ndadx,42\npx,7\n",
        })
    pheno_import([
        "--pheno-id", "sibling_pheno",
        "-p", str(sibling_ped),
        "-i", str(instruments),
        "--force",
        "-j", "1",
        "--person-column", "personId",
        "-o", str(pheno_dir / "sibling_pheno"),
        "--task-status-dir", str(root_path / "sibling_pheno" / "status"),
        "--task-log-dir", str(root_path / "sibling_pheno" / "log"),
    ])
    setup_directories(pheno_dir / "pheno_group", {
        "pheno_group.yaml": textwrap.dedent("""
            id: pheno_group
            name: Pheno Group
            type: group
            children:
              - study_1_pheno
              - sibling_pheno
        """),
    })
    instance.reload()
    return instance


@pytest.fixture
def pheno_group_instance(
    pheno_group_module: WGPFInstance,
    db: None,  # ruff: ignore[unused-function-argument]
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(pheno_group_module)
    for target in (
        "gpf_instance.gpf_instance.get_wgpf_instance",
        "datasets_api.permissions.get_wgpf_instance",
        "query_base.query_base.get_wgpf_instance",
    ):
        mocker.patch(target, return_value=pheno_group_module)
    return pheno_group_module


@pytest.fixture
def grant_on_study_1_pheno(user: User) -> User:
    add_group_perm_to_user("study_1_pheno", user)
    return user


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
