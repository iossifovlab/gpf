import json

from django.shortcuts import get_object_or_404

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status

from query_state_save.models import QueryState
from query_state_save.serializers import QueryStateSerializer


class QueryStateSaveView(views.APIView):

    def post(self, request):
        serializer = QueryStateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

        print("save type", type(serializer.data["data"]))

        query_state = QueryState.objects.create(
            data=json.dumps(serializer.data["data"]),
            page=serializer.data["page"])

        return Response({
           "url": query_state.uuid
        }, status=status.HTTP_201_CREATED)


class QueryStateLoadView(views.APIView):

    def post(self, request):
        query_state = get_object_or_404(QueryState, uuid=request.data["uuid"])
        print(query_state.data, type(query_state.data))

        return Response({
            "data": json.loads(query_state.data),
            "page": query_state.page
        }, status=status.HTTP_200_OK)
