from django.urls import re_path

from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet, add_group_to_dataset, \
    remove_group_from_dataset

router = SimpleRouter(trailing_slash=False)
router.register(r"groups", GroupsViewSet, basename="groups")

urlpatterns = [
    re_path(r"^groups/grant-permission/?$", add_group_to_dataset),
    re_path(r"^groups/revoke-permission/?$", remove_group_from_dataset),
] + router.urls
