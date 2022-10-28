from django.db.models import Count, Q
from rest_framework import viewsets, permissions, mixins, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import GroupSerializer, GroupRetrieveSerializer, \
    GroupCreateSerializer
from datasets_api.models import Dataset
from django.contrib.auth.models import Group


class GroupsViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "list" or self.action == "retrieve":
            serializer_class = GroupRetrieveSerializer
        elif self.action == "create":
            serializer_class = GroupCreateSerializer

        return serializer_class

    def get_queryset(self):
        # Get groups that have users or datasets tagged with it
        return Group.objects.annotate(
            users_count=Count("user"), datasets_count=Count("dataset")
        ).filter(
            Q(users_count__gt=0) | Q(datasets_count__gt=0)
        ).order_by("name")


@api_view(["POST"])
def add_group_to_dataset(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not ("datasetId" in request.data and "groupName" in request.data):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(dataset_id=request.data["datasetId"])
    group, _ = Group.objects.get_or_create(name=request.data["groupName"])
    dataset.groups.add(group)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def remove_group_from_dataset(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not ("datasetId" in request.data and "groupId" in request.data):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(dataset_id=request.data["datasetId"])
    group = Group.objects.get(pk=request.data["groupId"])
    if group.name in dataset.default_groups:
        return Response(status=status.HTTP_403_FORBIDDEN)
    dataset.groups.remove(group)
    return Response(status=status.HTTP_200_OK)
