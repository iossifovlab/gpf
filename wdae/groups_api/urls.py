from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet
from groups_api.views import GrantPermissionToGroupView
from groups_api.views import RevokePermissionToGroupView
from django.conf.urls import url


router = SimpleRouter(trailing_slash=False)
router.register(r'', GroupsViewSet, base_name='groups')

urlpatterns = [
    url(r'^/grant-permission$', GrantPermissionToGroupView.as_view(),
        name="grant_permission"),
    url(r'^/revoke-permission$', RevokePermissionToGroupView.as_view(),
        name="revoke_permission"),
] + router.urls
