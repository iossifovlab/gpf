from django.urls import re_path
from rest_framework.routers import SimpleRouter

from groups_api.views import (
    GroupsViewSet,
    add_group_to_dataset,
    add_user_to_group,
    remove_group_from_dataset,
    remove_user_from_group,
)

router = SimpleRouter(trailing_slash=False)
router.register(r"groups", GroupsViewSet, basename="groups")

urlpatterns = [
    re_path(r"^groups/grant-permission/?$", add_group_to_dataset),
    re_path(r"^groups/revoke-permission/?$", remove_group_from_dataset),
    re_path(r"^groups/add-user/?$", add_user_to_group),
    re_path(r"^groups/remove-user/?$", remove_user_from_group),
] + router.urls
