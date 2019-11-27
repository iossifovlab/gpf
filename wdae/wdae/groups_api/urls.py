from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet
from groups_api.views import GrantPermissionToGroupView
from groups_api.views import RevokePermissionToGroupView
from groups_api.views import GroupUsersManagementView
from groups_api.views import GroupDatasetsManagementView
from django.conf.urls import url


router = SimpleRouter(trailing_slash=False)
router.register(r'groups', GroupsViewSet, basename='groups')

urlpatterns = [
    url(r'^groups/grant-permission$', GrantPermissionToGroupView.as_view(),
        name="grant_permission"),
    url(r'^groups/revoke-permission$', RevokePermissionToGroupView.as_view(),
        name="revoke_permission"),
    url(r'^groups/(\d+)/user/(\d+)', GroupUsersManagementView.as_view(),
        name='group_users_management'),
    url(r'^groups/(\d+)/dataset/([\w ]+)',
        GroupDatasetsManagementView.as_view(),
        name='group_datasets_management'),

] + router.urls
