from rest_framework import pagination
from rest_framework.response import Response  # type: ignore


class WdaePageNumberPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(data)
