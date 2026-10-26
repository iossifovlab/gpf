# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import pytest
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth.models import Group, User
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from users_api.models import WdaeUser

from genotype_browser.views import GenotypeBrowserQueryDownloadView
from gpf.genotype_storage import genotype_storage_registry
from gpf.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from gpf.query_variants.query_runners import QueryResult

QUERY_VARIANTS_DOWNLOAD_URL = "/api/v3/genotype_browser/query-download"
DOWNLOAD_LIMIT = GenotypeBrowserQueryDownloadView.DOWNLOAD_LIMIT


@dataclass
class StorageLimits:
    """The limits that the storage layer saw in one download."""

    kwargs_limits: list[int | None] = field(default_factory=list)
    result_limits: list[int] = field(default_factory=list)


@pytest.fixture
def storage_limits(monkeypatch: pytest.MonkeyPatch) -> StorageLimits:
    """Record the limit kwarg and the QueryResult limit of each query."""
    limits = StorageLimits()
    original_query_variants = GenotypeStorageRegistry.query_variants

    def spy_query_variants(
        self: GenotypeStorageRegistry,
        study_kwargs: list[tuple[str, dict[str, Any]]],
        limit: int | None = None,
    ) -> Iterable[Any]:
        limits.kwargs_limits.append(study_kwargs[0][1].get("limit"))
        return original_query_variants(self, study_kwargs, limit=limit)

    class SpyQueryResult(QueryResult):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            limits.result_limits.append(self.limit)

    monkeypatch.setattr(
        GenotypeStorageRegistry, "query_variants", spy_query_variants)
    monkeypatch.setattr(
        genotype_storage_registry, "QueryResult", SpyQueryResult)
    return limits


def download(client: Client, max_variants_count: Any) -> None:
    data: dict[str, Any] = {"datasetId": "t4c8_study_1"}
    if max_variants_count is not None:
        data["maxVariantsCount"] = max_variants_count
    response = client.post(
        QUERY_VARIANTS_DOWNLOAD_URL,
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    list(response.streaming_content)  # type: ignore


@pytest.mark.parametrize(
    "max_variants_count",
    [1_000_000_000, -1, 0, -5, "many", None, "\u00b2", "\u2460"],
)
def test_download_limit_is_capped_for_ordinary_user(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
    storage_limits: StorageLimits,
    max_variants_count: Any,
) -> None:
    add_group_perm_to_user("t4c8_study_1", user)

    download(user_client, max_variants_count)

    assert storage_limits.kwargs_limits == [DOWNLOAD_LIMIT]
    assert storage_limits.result_limits == [DOWNLOAD_LIMIT]


def test_download_limit_below_cap_is_honoured_for_ordinary_user(
    user: User,
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
    storage_limits: StorageLimits,
) -> None:
    add_group_perm_to_user("t4c8_study_1", user)

    download(user_client, 1)

    assert storage_limits.kwargs_limits == [1]
    assert storage_limits.result_limits == [1]


@pytest.fixture
def unlimited_user(user: User) -> User:
    group, _ = Group.objects.get_or_create(
        name=WdaeUser.UMLIMITED_DOWNLOAD_GROUP)
    user.groups.add(group)
    add_group_perm_to_user("t4c8_study_1", user)
    return user


@pytest.fixture
def unlimited_user_client(
    unlimited_user: User,  # ruff: ignore[unused-function-argument]
    user_client: Client,
) -> Client:
    return user_client


@pytest.mark.parametrize(
    ("client_fixture", "max_variants_count", "expected"),
    [
        ("admin_client", -1, (None, -1)),
        ("admin_client", None, (None, -1)),
        ("admin_client", 1_000_000_000, (1_000_000_000, 1_000_000_000)),
        ("admin_client", 100.0, (100, 100)),
        ("admin_client", "100", (100, 100)),
        ("unlimited_user_client", -1, (None, -1)),
        ("unlimited_user_client", None, (None, -1)),
        ("unlimited_user_client", 1_000_000_000,
         (1_000_000_000, 1_000_000_000)),
    ],
)
def test_download_limit_for_privileged_user(
    request: pytest.FixtureRequest,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
    storage_limits: StorageLimits,
    client_fixture: str,
    max_variants_count: Any,
    expected: tuple[int | None, int],
) -> None:
    kwargs_limit, result_limit = expected
    client = request.getfixturevalue(client_fixture)

    download(client, max_variants_count)

    assert storage_limits.kwargs_limits == [kwargs_limit]
    assert storage_limits.result_limits == [result_limit]
