import codecs
import io
import logging
import math
import os
import time
from urllib.parse import urlparse

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PlainTextParser(BaseParser):
    """Plaintext parser."""

    media_type = "text/plain"

    def parse(
        self, stream: io.IOBase,
        _media_type: str | None = None,
        parser_context: dict | None = None,
    ) -> str:
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)
        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            return decoded_stream.read()
        except ValueError as exc:
            raise ParseError(f"Plain text parse error - {exc!s}") from exc


def _token_time(sentry_token: str) -> float | None:
    """Return the issue time of a token in seconds, or None if unreadable."""
    _, sep, value = sentry_token.split("&")[0].partition("=")
    if not sep:
        return None
    try:
        time_issued = float(value) / pow(10, 6)
    except ValueError:
        return None
    if not math.isfinite(time_issued):
        return None
    return time_issued


def _body_too_large(request: Request) -> bool:
    """Check the declared body size against DATA_UPLOAD_MAX_MEMORY_SIZE."""
    limit = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    if limit is None:
        return False
    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        content_length = 0
    return content_length > limit


@api_view(["POST"])
@parser_classes([PlainTextParser])
def sentry(request: Request) -> Response:
    """Tunnel Sentry requests from the frontend."""
    expiration_time = 60 * 60  # in seconds
    clock_skew = 60  # in seconds, between the browser and the server
    sentry_token = request.COOKIES.get("sentry_token")
    if not sentry_token:
        return Response({}, status.HTTP_200_OK)
    time_issued = _token_time(sentry_token)
    curr_time = time.time()
    if (
        time_issued is None
        or time_issued > curr_time + clock_skew
        or time_issued + expiration_time <= curr_time
    ):
        return Response({}, status.HTTP_401_UNAUTHORIZED)

    if _body_too_large(request):
        return Response({}, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    dsn = os.environ.get("GPFJS_SENTRY_DSN")
    if not dsn:
        return Response({}, status.HTTP_200_OK)
    fake_dsn = "https://0@0.ingest.sentry.io/0"  # gpfjs: main.ts
    project_id = urlparse(dsn).path.strip("/")
    sentry_host = dsn.split("@")[1].split("/")[0]
    upstream_sentry_url = f"https://{sentry_host}/api/{project_id}/envelope/"
    try:
        requests.post(
            upstream_sentry_url,
            data=request.data.replace(fake_dsn, dsn).encode(),
            timeout=5,
        )
    except requests.RequestException as exc:
        logger.warning("sentry tunnel: upstream request failed: %s", exc)
        return Response({}, status.HTTP_502_BAD_GATEWAY)
    return Response({}, status.HTTP_200_OK)
