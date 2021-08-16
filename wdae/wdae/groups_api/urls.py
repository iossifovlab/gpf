from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet
from groups_api.views import GrantPermissionToGroupView
from groups_api.views import RevokePermissionToGroupView
from groups_api.views import GroupUsersManagementView
from groups_api.views import GroupDatasetsManagementView
from django.urls import re_path


router = SimpleRouter(trailing_slash=False)
router.register(r"groups", GroupsViewSet, basename="groups")

urlpatterns = [
    re_path(
        r"^groups/grant-permission/?$",
        GrantPermissionToGroupView.as_view(),
        name="grant_permission",
    ),
    re_path(
        r"^groups/revoke-permission/?$",
        RevokePermissionToGroupView.as_view(),
        name="revoke_permission",
    ),
    re_path(
        r"^groups/(\d+)/user/(\d+)",
        GroupUsersManagementView.as_view(),
        name="group_users_management",
    ),
    re_path(
        r"^groups/(\d+)/dataset/([\w ]+)",
        GroupDatasetsManagementView.as_view(),
        name="group_datasets_management",
    ),
] + router.urls
