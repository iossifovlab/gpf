import codecs
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

import json
import os
import requests
from urllib.parse import urlparse


class PlainTextParser(BaseParser):
    media_type = "text/plain"

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            text_content = decoded_stream.read()
            return text_content
        except ValueError as exc:
            raise ParseError("Plain text parse error - %s" % str(exc))


@api_view(["POST"])
@parser_classes([PlainTextParser])
def sentry(request):
    data = request.data.split("\n")
    header = json.loads(data[0])
    dsn = urlparse(header["dsn"])
    project_id = dsn.path.strip("/")
    sentry_host = os.environ.get("SENTRY_HOST")
    upstream_sentry_url = f"https://{sentry_host}/api/{project_id}/envelope/"
    requests.post(upstream_sentry_url, data=request.data.encode(), timeout=30)
    return Response({}, status.HTTP_200_OK)
