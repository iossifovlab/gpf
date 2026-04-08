from typing import Any

from rest_framework import pagination, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class WdaePageNumberPagination(pagination.PageNumberPagination):
    """Custom pagination class that handles empty pages."""

    page_size_query_param = "page_size"

    def paginate_queryset(
        self,
        queryset: Any,
        request: Request,
        view: APIView | None = None,
    ) -> list[Any] | None:
        """Paginate and handle empty pages by returning 204."""
        try:
            result: list[Any] | None = super().paginate_queryset(
                queryset, request, view=view,
            )
        except NotFound:
            return []

        return result

    def get_paginated_response(self, data: list[Any]) -> Response:
        if len(data) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data)
