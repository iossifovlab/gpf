from __future__ import unicode_literals
from guardian.models import Group
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status

from groups_api.serializers import GroupSerializer
from groups_api.serializers import GroupRetrieveSerializer
from groups_api.serializers import PermissionChangeSerializer
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm


class GroupsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'list' or self.action == 'retrieve':
            serializer_class = GroupRetrieveSerializer

        return serializer_class

    def get_queryset(self):
        # Either the group has users or has 'view' permission to some dataset
        return Group.objects \
            .annotate(users_count=Count('user')) \
            .filter(
                Q(users_count__gt=0) |
                Q(groupobjectpermission__permission__codename='view'))


class GrantPermissionToGroupView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        serializer = PermissionChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=serializer.data['datasetId'])
        group = Group.objects.get(pk=serializer.data['groupId'])

        assign_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)


class RevokePermissionToGroupView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        serializer = PermissionChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=serializer.data['datasetId'])
        group = Group.objects.get(pk=serializer.data['groupId'])

        if group.name in dataset.default_groups:
            return Response(status=status.HTTP_403_FORBIDDEN)

        remove_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)

