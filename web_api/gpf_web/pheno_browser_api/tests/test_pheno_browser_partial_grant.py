# pylint: disable=W0621,C0114,C0116,W0212,W0613
import csv
import io
from collections.abc import Generator, Iterator
from datetime import timedelta
from typing import Any, cast

import pytest
import pytest_mock
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from django.test import Client, override_settings
from django.utils import timezone
from gpf_instance.extension import GPFTool
from gpf_instance.gpf_instance import WGPFInstance
from oauth2_provider.models import Application, get_access_token_model
from rest_framework import status
from studies.study_wrapper import WDAEAbstractStudy

from pheno_browser_api.pheno_browser_helper import BasePhenoBrowserHelper

MEASURES_COUNT_URL = "/api/v3/pheno_browser/measures_count"
DOWNLOAD_URL = "/api/v3/pheno_browser/download"
STUDY_1_PHENO_MEASURE_COUNT = 8


@pytest.fixture
def grant_on_two_leaves(user: User) -> User:
    add_group_perm_to_user("study_1_pheno", user)
    add_group_perm_to_user("sibling_pheno", user)
    return user


@pytest.fixture
def group_granted_client(oauth_app: Application) -> Client:
    other = get_user_model().objects.create(
        email="other@example.com",
        name="Other",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    other.set_password("secret")
    other.save()
    add_group_perm_to_user("pheno_group", other)  # type: ignore[arg-type]
    get_access_token_model()(
        user=other,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="other-token",  # ruff: ignore[hardcoded-password-func-arg]
        application=oauth_app,
    ).save()
    return Client(HTTP_AUTHORIZATION="Bearer other-token")


def _download(client: Client, data: dict[str, str]) -> list[dict[str, str]]:
    response = cast(StreamingHttpResponse, client.get(DOWNLOAD_URL, data))
    assert response.status_code == status.HTTP_200_OK
    content = b"".join(
        cast(Iterator[bytes], response.streaming_content)).decode()
    return list(csv.DictReader(io.StringIO(content)))


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_measures_count_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get(f"{MEASURES_COUNT_URL}?dataset_id=pheno_group")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == STUDY_1_PHENO_MEASURE_COUNT


@pytest.mark.usefixtures("grant_on_two_leaves", "pheno_group_instance")
def test_measures_count_under_a_grant_on_two_of_three_leaves(
    user_client: Client,
) -> None:
    response = user_client.get(f"{MEASURES_COUNT_URL}?dataset_id=pheno_group")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == STUDY_1_PHENO_MEASURE_COUNT + 1


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_measures_count_etag_differs_between_partial_and_full_grant(
    user_client: Client,
    group_granted_client: Client,
) -> None:
    url = f"{MEASURES_COUNT_URL}?dataset_id=pheno_group"

    partial = user_client.get(url)
    full = group_granted_client.get(url)

    assert partial.status_code == status.HTTP_200_OK
    assert full.status_code == status.HTTP_200_OK
    assert partial["ETag"] != full["ETag"]


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.usefixtures(
    "grant_on_study_1_pheno", "pheno_group_instance", "reset_flags")
def test_download_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    rows = _download(user_client, {"dataset_id": "pheno_group"})

    assert rows
    assert not set(rows[0]) & {"sib.age", "thr.score"}
    assert not {row["person_id"] for row in rows} & {
        "momx", "dadx", "px", "momy", "dady", "py"}


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.usefixtures(
    "grant_on_two_leaves", "pheno_group_instance", "reset_flags")
def test_download_under_a_grant_on_two_of_three_leaves(
    user_client: Client,
) -> None:
    rows = _download(user_client, {"dataset_id": "pheno_group"})

    assert "sib.age" in rows[0]
    assert "thr.score" not in rows[0]
    assert not {row["person_id"] for row in rows} & {"momy", "dady", "py"}


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.usefixtures(
    "grant_on_study_1_pheno", "pheno_group_instance", "reset_flags")
def test_download_head_of_another_leaf_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.head(
        DOWNLOAD_URL, {"dataset_id": "pheno_group", "instrument": "sib"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.usefixtures(
    "grant_on_two_leaves", "pheno_group_instance", "reset_flags")
def test_download_head_under_a_grant_on_two_of_three_leaves(
    user_client: Client,
) -> None:
    allowed = user_client.head(
        DOWNLOAD_URL, {"dataset_id": "pheno_group", "instrument": "sib"})
    hidden = user_client.head(
        DOWNLOAD_URL, {"dataset_id": "pheno_group", "instrument": "thr"})

    assert allowed.status_code == status.HTTP_200_OK
    assert hidden.status_code == status.HTTP_404_NOT_FOUND


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.usefixtures(
    "grant_on_t4c8_study_1", "pheno_group_instance", "reset_flags")
def test_browser_routes_of_a_genotype_parent_under_partial_grant(
    user_client: Client,
) -> None:
    count = user_client.get(f"{MEASURES_COUNT_URL}?dataset_id=pheno_parent")
    rows = _download(user_client, {"dataset_id": "pheno_parent"})
    head = user_client.head(
        DOWNLOAD_URL, {"dataset_id": "pheno_parent", "instrument": "thr"})

    assert count.json()["count"] == STUDY_1_PHENO_MEASURE_COUNT
    assert not set(rows[0]) & {"sib.age", "thr.score"}
    assert not {row["person_id"] for row in rows} & {"px", "py"}
    assert head.status_code == status.HTTP_404_NOT_FOUND


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.parametrize("dataset_id", ["pheno_group", "pheno_parent"])
@pytest.mark.usefixtures("pheno_group_instance", "reset_flags")
def test_browser_routes_under_a_grant_on_the_parent(
    user: User,
    user_client: Client,
    dataset_id: str,
) -> None:
    add_group_perm_to_user(dataset_id, user)

    count = user_client.get(f"{MEASURES_COUNT_URL}?dataset_id={dataset_id}")
    rows = _download(user_client, {"dataset_id": dataset_id})
    head = user_client.head(
        DOWNLOAD_URL, {"dataset_id": dataset_id, "instrument": "thr"})

    assert count.json()["count"] == STUDY_1_PHENO_MEASURE_COUNT + 2
    assert {"sib.age", "thr.score"} <= set(rows[0])
    assert {"px", "py"} <= {row["person_id"] for row in rows}
    assert head.status_code == status.HTTP_200_OK


@override_settings(FEATURE_FLAGS={"pheno_browser_download": True})
@pytest.mark.parametrize("method", ["get", "head"])
@pytest.mark.usefixtures(
    "grant_on_study_1_pheno", "pheno_group_instance", "reset_flags")
def test_download_etag_differs_between_partial_and_full_grant(
    user_client: Client,
    group_granted_client: Client,
    method: str,
) -> None:
    data = {"dataset_id": "pheno_group", "instrument": "i1"}

    partial = getattr(user_client, method)(DOWNLOAD_URL, data)
    full = getattr(group_granted_client, method)(DOWNLOAD_URL, data)

    assert partial.status_code == status.HTTP_200_OK
    assert full.status_code == status.HTTP_200_OK
    assert partial["ETag"] != full["ETag"]


class _StubPhenoBrowserHelper(BasePhenoBrowserHelper):
    """A pheno browser helper of an extension that answers plain values."""

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError

    def get_instruments(self) -> list[str]:
        raise NotImplementedError

    def get_measures_info(self) -> dict[str, Any]:
        raise NotImplementedError

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def search_measures(
        self, data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_measure_ids(
        self, data: dict[str, Any],
    ) -> Generator[str, None, None]:
        raise NotImplementedError

    def measures_count_status(self, data: dict[str, Any]) -> str:
        raise NotImplementedError

    def get_count(self, data: dict[str, Any]) -> int:
        del data
        return 0

    def get_image(self, image_path: str) -> tuple[bytes | None, str | None]:
        raise NotImplementedError


@pytest.mark.usefixtures("grant_on_study_1_pheno")
def test_measures_count_with_an_extension_helper_under_partial_grant_is_403(
    user_client: Client,
    pheno_group_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    # A real helper, not a Mock: DRF renders a Mock attribute by calling
    # its ``tolist`` without end, so a regression would exhaust memory.
    extension = mocker.Mock()
    extension.get_tool.return_value = _StubPhenoBrowserHelper()
    mocker.patch.dict(pheno_group_instance.extensions, {"fake": extension})

    response = user_client.get(f"{MEASURES_COUNT_URL}?dataset_id=pheno_group")

    assert response.status_code == status.HTTP_403_FORBIDDEN
