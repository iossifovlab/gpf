from guardian.models import Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from groups_api.serializers import GroupSerializer


class GroupsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    permission_classes = (permissions.IsAdminUser,)
