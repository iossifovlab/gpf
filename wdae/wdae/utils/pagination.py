from rest_framework import pagination, status  # type: ignore
from rest_framework.exceptions import NotFound
from rest_framework.response import Response  # type: ignore


class WdaePageNumberPagination(pagination.PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        """Paginate and handle empty pages by returning 204."""
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:
            return []

    def get_paginated_response(self, data):
        if len(data) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data)
