from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status

from .serializers import GroupSerializer
from .serializers import GroupRetrieveSerializer
from .serializers import PermissionChangeSerializer
from .serializers import PermissionRevokeSerializer
from .serializers import GroupUserPermissionSerializer
from .serializers import GroupDatasetPermissionSerializer
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
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
            print(serializer.errors)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=serializer.data['datasetId'])
        group = Group.objects.get(name=serializer.data['groupName'])

        assign_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)


class RevokePermissionToGroupView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        serializer = PermissionRevokeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=serializer.data['datasetId'])
        group = Group.objects.get(pk=serializer.data['groupId'])

        if group.name in dataset.default_groups:
            return Response(status=status.HTTP_403_FORBIDDEN)

        remove_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)


class GroupUsersManagementView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = GroupUserPermissionSerializer

    def post(self, request, group_id, user_id):
        data = {'groupId': group_id, 'userId': user_id}
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.get(user_id=user_id)
        group = Group.objects.get(pk=group_id)

        user.groups.add(group)

        return Response(status=status.HTTP_200_OK)

    def delete(self, request, group_id, user_id):
        data = {'groupId': group_id, 'userId': user_id}
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.get(user_id=user_id)
        group = Group.objects.get(pk=group_id)

        user.groups.add(group)

        return Response(status=status.HTTP_200_OK)


class GroupDatasetsManagementView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = GroupDatasetPermissionSerializer

    def post(self, request, group_id, dataset_id):
        data = {'groupId': group_id, 'datasetId': dataset_id}
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=dataset_id)
        group = Group.objects.get(pk=group_id)

        assign_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)

    def delete(self, request, group_id, dataset_id):
        data = {'groupId': group_id, 'datasetId': dataset_id}
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.get(dataset_id=dataset_id)
        group = Group.objects.get(pk=group_id)

        if group.name in dataset.default_groups:
            return Response(status=status.HTTP_403_FORBIDDEN)

        remove_perm('view', group, dataset)

        return Response(status=status.HTTP_200_OK)
