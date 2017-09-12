from guardian.models import Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from groups_api.serializers import GroupSerializer
from groups_api.serializers import GroupRetrieveSerializer


class GroupsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'list' or self.action == 'retrieve':
            serializer_class = GroupRetrieveSerializer

        return serializer_class

