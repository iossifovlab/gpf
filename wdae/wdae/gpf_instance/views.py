from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from dae import __version__ as VERSION


@api_view(["GET"])
def version(request: Request) -> Response:
    """Get GPF version."""
    return Response(
        {"version": VERSION},
        status=status.HTTP_200_OK
    )
