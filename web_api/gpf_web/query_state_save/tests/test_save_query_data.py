# pylint: disable=C0116

import json
from collections.abc import Callable
from typing import Any

import pytest
from rest_framework import status

from query_state_save.models import PAGE_TYPE_OPTIONS


def test_save_endpoint(
    query_save: Callable[[Any, str, str], str | None],
    simple_query_data: dict[str, Any],
) -> None:
    url_code = query_save(simple_query_data, "genotype", "user")

    assert url_code != ""


@pytest.mark.parametrize("page_type", PAGE_TYPE_OPTIONS)
def test_load_endpoint(
    query_save: Callable[[Any, str, str], str | None],
    query_load: Callable[[str], Any],
    simple_query_data: dict[str, Any],
    page_type: str,
) -> None:
    url_code = query_save(simple_query_data, page_type, "user")
    assert url_code is not None

    loaded = query_load(url_code)

    assert loaded["data"] == simple_query_data
    assert loaded["page"] == page_type


@pytest.mark.usefixtures("db")
def test_invalid_page_fails(
    user_client: Any, simple_query_data: dict[str, Any],
) -> None:
    url = "/api/v3/query_state/save"
    query = {"data": simple_query_data, "page": "alabala", "origin": "user"}

    response = user_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
