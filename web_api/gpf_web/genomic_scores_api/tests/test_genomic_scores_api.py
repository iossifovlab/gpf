# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import threading
from typing import Any

import pytest
from datasets_api import permissions
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from utils import cached_response


@pytest.fixture(autouse=True)
def _clear_cached_response() -> None:
    cached_response._CACHE.clear()


def test_get_genomic_scores(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)

    data = response.json()
    assert sorted([gs["score"] for gs in data]) == ["score_one"]


def test_get_genomic_scores_cache_control(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    assert response.headers["Cache-Control"] == "public, max-age=3600"


def test_get_genomic_scores_memo_hit(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = "/api/v3/genomic_scores"

    render_calls = 0
    original_render = cached_response.JSONRenderer.render

    def counting_render(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal render_calls
        render_calls += 1
        return original_render(self, *args, **kwargs)

    monkeypatch.setattr(
        cached_response.JSONRenderer, "render", counting_render,
    )

    first = user_client.get(url)
    second = user_client.get(url)

    assert first.status_code == status.HTTP_200_OK, repr(first.content)
    assert second.status_code == status.HTTP_200_OK, repr(second.content)
    assert first.content == second.content
    assert render_calls == 1


def test_get_genomic_scores_reload_invalidates(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bumping the instance timestamp re-renders and changes the ETag."""
    url = "/api/v3/genomic_scores"

    render_calls = 0
    original_render = cached_response.JSONRenderer.render

    def counting_render(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal render_calls
        render_calls += 1
        return original_render(self, *args, **kwargs)

    monkeypatch.setattr(
        cached_response.JSONRenderer, "render", counting_render,
    )

    first = user_client.get(url)
    assert first.status_code == status.HTTP_200_OK, repr(first.content)
    assert render_calls == 1

    # Simulate an instance reload by advancing the load timestamp.  Both
    # the cache key (in cached_response) and the ETag (computed by
    # datasets_api.permissions.get_instance_timestamp_etag) read this
    # timestamp, so both must observe the bump in lockstep.
    original_timestamp = cached_response.get_instance_timestamp

    def bumped_timestamp(*args, **kwargs):  # type: ignore[no-untyped-def]
        return original_timestamp(*args, **kwargs) + 1000.0

    monkeypatch.setattr(
        cached_response, "get_instance_timestamp", bumped_timestamp,
    )
    monkeypatch.setattr(
        permissions, "get_instance_timestamp", bumped_timestamp,
    )

    second = user_client.get(url)
    assert second.status_code == status.HTTP_200_OK, repr(second.content)
    assert render_calls == 2
    assert first.content == second.content
    assert first.headers["ETag"] != second.headers["ETag"]


def test_cached_json_response_concurrent_cold_cache(
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    """Concurrent cold-cache callers all get the byte-identical render."""
    payload = [{"score": "score_one", "value": list(range(100))}]

    def build() -> list[dict[str, Any]]:
        return payload

    reference = cached_response.JSONRenderer().render(payload)

    barrier = threading.Barrier(8)
    results: list[bytes] = []
    results_lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        response = cached_response.cached_json_response(
            "concurrent_instance", build,
        )
        with results_lock:
            results.append(response.content)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 8
    assert all(body == reference for body in results)


def test_get_genomic_scores_if_none_match_304(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores"
    first = user_client.get(url)
    assert first.status_code == status.HTTP_200_OK, repr(first.content)
    etag = first.headers["ETag"]

    second = user_client.get(url, HTTP_IF_NONE_MATCH=etag)
    assert second.status_code == status.HTTP_304_NOT_MODIFIED


def test_get_score_descs_all(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores/score_descs"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    data = response.json()
    assert sorted([sd["name"] for sd in data]) == ["score_one"]


def test_get_score_descs_single(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores/score_descs/score_one"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    data = response.json()
    assert [sd["name"] for sd in data] == ["score_one"]


def test_get_score_descs_unknown_404(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/genomic_scores/score_descs/no_such_score"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_score_descs_memo_hit_keyed_by_score_id(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    render_calls = 0
    original_render = cached_response.JSONRenderer.render

    def counting_render(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal render_calls
        render_calls += 1
        return original_render(self, *args, **kwargs)

    monkeypatch.setattr(
        cached_response.JSONRenderer, "render", counting_render,
    )

    all_url = "/api/v3/genomic_scores/score_descs"
    single_url = "/api/v3/genomic_scores/score_descs/score_one"

    first_all = user_client.get(all_url)
    second_all = user_client.get(all_url)
    first_single = user_client.get(single_url)
    second_single = user_client.get(single_url)

    assert first_all.content == second_all.content
    assert first_single.content == second_single.content
    # all and single are distinct cache keys (extra=score_id) -> 2 renders
    assert render_calls == 2
