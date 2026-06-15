"""In-process memoization of pre-rendered JSON responses.

``GET`` endpoints that serialize large, instance-static payloads (e.g.
the genomic scores registry with all of its histograms) are expensive
to re-render on every request even though the result only changes when
the GPF instance is reloaded.

This module memoizes the *rendered JSON bytes* keyed by the instance id
and the instance-load timestamp, so the serialization runs once per
instance load.  The helper is designed to compose under the existing
``etag(get_instance_timestamp_etag)`` decorator: that decorator handles
conditional ``304`` short-circuiting before the view body runs, so the
build function here only ever executes for a ``200``.
"""
from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import Any

from django.http import HttpResponse
from gpf_instance.gpf_instance import get_instance_timestamp
from rest_framework.renderers import JSONRenderer

CACHE_CONTROL = "public, max-age=3600"

_MAX_ENTRIES = 2
_CACHE: dict[tuple[Any, ...], bytes] = {}
_CACHE_LOCK = Lock()


def _get_or_render(
    key: tuple[Any, ...], build: Callable[[], Any],
) -> bytes:
    """Return memoized JSON bytes for ``key``, rendering on a miss.

    ``build`` returns the plain-Python payload; it is serialized with
    DRF's :class:`JSONRenderer` so the bytes are byte-identical to what
    a DRF ``Response`` would have produced (numpy scalars included).

    The cache is bounded to ``_MAX_ENTRIES`` with simple
    insertion-order eviction; the key already includes the instance
    timestamp, so a reload naturally produces fresh entries.
    """
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

    body: bytes = JSONRenderer().render(build())

    with _CACHE_LOCK:
        _CACHE[key] = body
        while len(_CACHE) > _MAX_ENTRIES:
            oldest = next(iter(_CACHE))
            del _CACHE[oldest]
    return body


def cached_json_response(
    instance_id: str,
    build: Callable[[], Any],
    *extra: Any,
) -> HttpResponse:
    """Return a cached ``application/json`` response.

    The rendered body is memoized in-process keyed by
    ``(instance_id, get_instance_timestamp(), extra)``.  Including
    ``instance_id`` prevents cross-fixture leakage in tests; ``extra``
    carries any view-varying parameter (e.g. an optional path segment).

    The response carries ``Cache-Control: public, max-age=3600``.
    """
    key = (instance_id, get_instance_timestamp(), *extra)
    body = _get_or_render(key, build)
    response = HttpResponse(body, content_type="application/json")
    response["Cache-Control"] = CACHE_CONTROL
    return response
