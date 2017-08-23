from guardian.models import Group
from rest_framework import viewsets
from rest_framework import permissions
from groups_api.serializers import GroupSerializer


class GroupsViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    permission_classes = (permissions.IsAdminUser,)
