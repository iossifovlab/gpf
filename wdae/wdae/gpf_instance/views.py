from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from dae import __version__ as VERSION  # type: ignore


@api_view(["GET"])
def version(_request: Request) -> Response:
    """Get GPF version."""
    return Response(
        {"version": VERSION},
        status=status.HTTP_200_OK
    )


class DescriptionView(QueryBaseView):
    """Provide fetching and editing the main application description."""

    def get(
        self, request: Request
    ) -> Response:
        # pylint: disable=unused-argument
        """Collect the application description."""
        description_file = open(
            self.gpf_instance.get_main_description_path(),
            "r"
        )
        description = description_file.read()
        description_file.close()
        if description is None:
            return Response(
                {"error": "Description not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"description": description},
            status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        """Overwrite the application description."""
        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN
            )

        description_file = open(
            self.gpf_instance.get_main_description_path(),
            "w"
        )
        description_file.write(request.data.get("description"))
        description_file.close()

        return Response(status=status.HTTP_200_OK)


class AboutDescriptionView(QueryBaseView):
    """Provide fetching and editing the main application description."""

    def get(
        self, request: Request
    ) -> Response:
        # pylint: disable=unused-argument
        """Collect the application description."""
        description_file = open(
            self.gpf_instance.get_about_description_path(),
            "r"
        )
        description = description_file.read()
        description_file.close()
        if description is None:
            return Response(
                {"error": "Description not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"description": description},
            status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        """Overwrite the application description."""
        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN
            )

        description_file = open(
            self.gpf_instance.get_about_description_path(),
            "w"
        )
        description_file.write(request.data.get("description"))
        description_file.close()

        return Response(status=status.HTTP_200_OK)
