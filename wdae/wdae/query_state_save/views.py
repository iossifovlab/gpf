import json

from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.response import Response
from user_queries.models import UserQuery

from .models import QueryState
from .serializers import QueryStateSerializer


class QueryStateSaveView(views.APIView):
    def post(self, request):
        serializer = QueryStateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.error_messages, status=status.HTTP_400_BAD_REQUEST,
            )

        query_state = QueryState.objects.create(
            data=json.dumps(serializer.data["data"]),
            page=serializer.data["page"],
        )

        return Response(
            {"uuid": query_state.uuid}, status=status.HTTP_201_CREATED,
        )


class QueryStateLoadView(views.APIView):
    def post(self, request):
        query_state = get_object_or_404(QueryState, uuid=request.data["uuid"])

        return Response(
            {"data": json.loads(query_state.data), "page": query_state.page},
            status=status.HTTP_200_OK,
        )


class QueryStateDeleteView(views.APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        stored_queries = UserQuery.objects.filter(user=request.user)
        for user_stored_query in stored_queries:
            if str(user_stored_query.query.uuid) == request.data["uuid"]:
                user_stored_query.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_404_NOT_FOUND)
