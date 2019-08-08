import json

from django.shortcuts import get_object_or_404

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status

from .models import QueryState
from .serializers import QueryStateSerializer


class QueryStateSaveView(views.APIView):

    def post(self, request):
        serializer = QueryStateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

        query_state = QueryState.objects.create(
            data=json.dumps(serializer.data["data"]),
            page=serializer.data["page"])

        return Response({
           "uuid": query_state.uuid
        }, status=status.HTTP_201_CREATED)


class QueryStateLoadView(views.APIView):

    def post(self, request):
        query_state = get_object_or_404(QueryState, uuid=request.data["uuid"])

        return Response({
            "data": json.loads(query_state.data),
            "page": query_state.page
        }, status=status.HTTP_200_OK)
