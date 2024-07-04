
from datasets_api.permissions import get_instance_timestamp_etag
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from dae import __version__ as VERSION  # type: ignore


@api_view(["GET"])
@etag(get_instance_timestamp_etag)
def version(_request: Request) -> Response:
    """Get GPF version."""
    return Response(
        {"version": VERSION},
        status=status.HTTP_200_OK,
    )


class MarkdownFileView(QueryBaseView):
    """Provide fetching and editing markdown files."""

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
            with open(self.filepath, "r") as markdown_file:
                content = markdown_file.read()
        except FileNotFoundError:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
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
            with open(self.filepath, "w") as markdown_file:
                markdown_file.write(request.data.get("content"))
        except PermissionError:
            return Response(
                {"error": "Failed to write to file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_200_OK)


class DescriptionView(MarkdownFileView):
    """Provide fetching and editing the main application description."""

    def __init__(self) -> None:
        super().__init__()
        self.filepath = self.gpf_instance.get_main_description_path()


class AboutDescriptionView(MarkdownFileView):
    """Provide fetching and editing the main application description."""

    def __init__(self) -> None:
        super().__init__()
        self.filepath = self.gpf_instance.get_about_description_path()
