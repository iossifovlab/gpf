from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request 
from rest_framework.decorators import api_view
from utils.logger import LOGGER, request_logging_function_view
from dae import __version__ as VERSION


@request_logging_function_view(LOGGER)
@api_view(["GET"])
def version(request: Request) -> Response:
    """Get GPF version."""
    if request.method == "GET":
        return Response(
            {"version": VERSION},
            status=status.HTTP_200_OK
        )
    return Response(
        {
            "error":
            "You have no permission to edit, update or delete the gpf version."
        },
        status=status.HTTP_403_FORBIDDEN
    )
