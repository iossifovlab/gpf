from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet


router = SimpleRouter(trailing_slash=False)
router.register(r'', GroupsViewSet, base_name='groups')

urlpatterns = router.urls
