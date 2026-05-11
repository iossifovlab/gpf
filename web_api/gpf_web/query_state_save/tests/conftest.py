import functools
import json
from collections.abc import Callable
from typing import Any

import pytest
from rest_framework import status


def save_object(data: Any, page: str, origin: str, client: Any) -> str | None:
    """Helper function to save query state."""
    url = "/api/v3/query_state/save"
    query = {"data": data, "page": page, "origin": origin}
    response = client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    uuid_value: str | None = response.data.get("uuid")
    return uuid_value


def load_object(url_code: str, client: Any) -> Any:
    """Helper function to load query state."""
    url = "/api/v3/query_state/load"
    query = {"uuid": url_code}

    response = client.post(url, query, format="json")

    assert response.status_code == status.HTTP_200_OK

    return response.data


@pytest.fixture
def query_load(
    db: Any, user_client: Any,  # noqa: ARG001
) -> Callable[[str], Any]:

    return functools.partial(load_object, client=user_client)


@pytest.fixture
def query_save(
    db: Any, user_client: Any,  # noqa: ARG001
) -> Callable[[Any, str, str], str | None]:
    return functools.partial(save_object, client=user_client)


@pytest.fixture
def simple_query_data() -> dict[str, Any]:
    return {"some": "data", "list": [1, 2, 3]}
