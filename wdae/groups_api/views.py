from guardian.models import Group
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import mixins
from groups_api.serializers import GroupSerializer
from groups_api.serializers import GroupRetrieveSerializer


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
