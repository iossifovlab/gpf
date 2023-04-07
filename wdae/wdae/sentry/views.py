import os
import codecs
from urllib.parse import urlparse

import requests

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser


class PlainTextParser(BaseParser):
    """Plaintext parser."""

    media_type = "text/plain"

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)
        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            text_content = decoded_stream.read()
            return text_content
        except ValueError as exc:
            raise ParseError(f"Plain text parse error - {str(exc)}") from exc


@api_view(["POST"])
@parser_classes([PlainTextParser])
def sentry(request):
    """Tunnel Sentry requests from the frontend."""
    dsn = os.environ.get("WDAE_SENTRY_DSN")
    fake_dsn = "https://0@0.ingest.sentry.io/0"  # gpfjs: main.ts
    project_id = urlparse(dsn).path.strip("/")
    sentry_host = dsn.split("@")[1].split("/")[0]
    upstream_sentry_url = f"https://{sentry_host}/api/{project_id}/envelope/"
    requests.post(
        upstream_sentry_url,
        data=request.data.replace(fake_dsn, dsn).encode(),
        timeout=30
    )
    return Response({}, status.HTTP_200_OK)
