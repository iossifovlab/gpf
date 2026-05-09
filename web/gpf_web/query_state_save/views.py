import json
from datetime import date
from typing import Any, cast

from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.request import Request
from rest_framework.response import Response
from user_queries.models import UserQuery

from .models import QueryState
from .serializers import QueryStateSerializer


class QueryStateSaveView(views.APIView):
    """Query state save view."""
    def post(self, request: Request) -> Response:
        """Save query state"""
        serializer = QueryStateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.error_messages, status=status.HTTP_400_BAD_REQUEST,
            )

        data = cast(dict[str, Any], serializer.data)
        # pylint: disable=unsubscriptable-object
        query_state = QueryState.objects.create(
            data=json.dumps(data["data"]),
            page=data["page"],
            origin=data["origin"],
            timestamp=date.today(),
        )

        return Response(
            {"uuid": query_state.uuid}, status=status.HTTP_201_CREATED,
        )


class QueryStateLoadView(views.APIView):
    """Query state load view."""
    def post(self, request: Request) -> Response:
        """Get query state"""
        request_uuid: str = request.data["uuid"]  # pyright: ignore
        query_state = get_object_or_404(QueryState, uuid=request_uuid)

        return Response(
            {"data": json.loads(query_state.data), "page": query_state.page},
            status=status.HTTP_200_OK,
        )


class QueryStateDeleteView(views.APIView):
    """Query state delete view"""
    def post(self, request: Request) -> Response:
        """Delete saved query state"""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        stored_queries = UserQuery.objects.filter(user=request.user)
        for user_stored_query in stored_queries:
            request_uuid: str = request.data["uuid"]  # pyright: ignore
            if str(user_stored_query.query.uuid) == request_uuid:
                user_stored_query.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_404_NOT_FOUND)
