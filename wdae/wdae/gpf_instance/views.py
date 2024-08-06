from pathlib import Path
from typing import Any

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from dae import __version__ as VERSION  # type: ignore
from gpf_instance.gpf_instance import (
    calc_and_set_cacheable_hash,
    get_cacheable_hash,
)


@api_view(["GET"])
@etag(get_instance_timestamp_etag)
def version(_request: Request) -> Response:
    """Get GPF version."""
    return Response(
        {"version": VERSION},
        status=status.HTTP_200_OK,
    )


def get_description_etag(
    _request: Request, **_kwargs: dict[str, Any],
) -> str | None:
    return get_cacheable_hash("instance_description")


def get_about_etag(
    _request: Request, **_kwargs: dict[str, Any],
) -> str | None:
    return get_cacheable_hash("instance_about")


class MarkdownFileView(QueryBaseView):
    """Provide fetching and editing markdown files."""

    CONTENT_ID = "placeholder_id"

    def __init__(self) -> None:
        super().__init__()
        self.filepath: str | None = None

    def get(self, _request: Request) -> Response:
        # pylint: disable=unused-argument
        """Collect the application description."""
        if self.filepath is None:
            return Response(
                {"error": "Route incorrectly configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        try:
            content = Path(self.filepath).read_text()
        except FileNotFoundError:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_cacheable_hash(self.CONTENT_ID) is None:
            calc_and_set_cacheable_hash(self.CONTENT_ID, content)

        return Response(
            {"content": content},
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        """Overwrite the application description."""
        if self.filepath is None:
            return Response(
                {"error": "Route incorrectly configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the content."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            Path(self.filepath).write_text(request.data.get("content"))
        except PermissionError:
            return Response(
                {"error": "Failed to write to file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        calc_and_set_cacheable_hash(
            self.CONTENT_ID,
            request.data.get("content"),
        )
        return Response(status=status.HTTP_200_OK)


class DescriptionView(MarkdownFileView):
    """Provide fetching and editing the main application description."""

    CONTENT_ID = "instance_description"

    def __init__(self) -> None:
        super().__init__()
        self.filepath = self.gpf_instance.get_main_description_path()

    @method_decorator(etag(get_description_etag))
    def get(self, _request: Request) -> Response:
        return super().get(_request)


class AboutDescriptionView(MarkdownFileView):
    """Provide fetching and editing the main application description."""

    CONTENT_ID = "instance_about"

    def __init__(self) -> None:
        super().__init__()
        self.filepath = self.gpf_instance.get_about_description_path()

    @method_decorator(etag(get_about_etag))
    def get(self, _request: Request) -> Response:
        return super().get(_request)
