from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .serializers import GroupSerializer
from .serializers import GroupRetrieveSerializer
from .serializers import GroupCreateSerializer
from datasets_api.models import Dataset
from django.contrib.auth.models import Group


class GroupsViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "list" or self.action == "retrieve":
            serializer_class = GroupRetrieveSerializer
        elif self.action == "create":
            serializer_class = GroupCreateSerializer

        return serializer_class

    def get_queryset(self):
        return Group.objects.annotate(users_count=Count("user")).filter(
            Q(users_count__gt=0)  # Get groups that have users
        )


@api_view(["POST"])
def add_group_to_dataset(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not ("datasetId" in request.data and "groupName" in request.data):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(dataset_id=request.data["datasetId"])
    group, _ = Group.objects.get_or_create(name=request.data["groupName"])
    dataset.groups.add(group)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def remove_group_from_dataset(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not ("datasetId" in request.data and "groupId" in request.data):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(dataset_id=request.data["datasetId"])
    group = Group.objects.get(pk=request.data["groupId"])
    if group.name in dataset.default_groups:
        return Response(status=status.HTTP_403_FORBIDDEN)
    dataset.groups.remove(group)
    return Response(status=status.HTTP_200_OK)
